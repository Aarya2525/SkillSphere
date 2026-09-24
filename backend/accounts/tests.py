"""
API Validation and Centralized Error Handling Tests.
Stage 16: API Validation & Errors.

Verifies consistent, safe error formats across:
- 400 Validation and Parse errors
- 401 Authentication errors
- 403 Permission errors
- 404 Not Found errors
- 405 Method Not Allowed errors
- 415 Unsupported Media Type errors
- 429 Rate Limiting errors
- 500 Internal Server errors
- 502/503/504 AI assistant provider errors
- Shielding of tracebacks, file paths, and server secrets
"""
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, override_settings
from rest_framework import exceptions, status
from rest_framework.parsers import JSONParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.test import APIClient, APIRequestFactory
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from test_utils.base import FAST_HASHERS_OVERRIDE
from ai_assistant.providers.base import (
    AIConfigurationError,
    AIProviderError,
    AITimeoutError,
)

User = get_user_model()


class MockCrashView(APIView):
    """Test view that raises an unexpected internal server exception."""
    permission_classes = [AllowAny]

    def get(self, request):
        raise RuntimeError("Internal DB connection failed: super_secret_password_999")


class MockMediaView(APIView):
    """Test view that accepts only application/json."""
    parser_classes = [JSONParser]
    permission_classes = [AllowAny]

    def post(self, request):
        _ = request.data
        return Response({"status": "ok"})


class MockThrottledView(APIView):
    """Test view with a low throttle limit."""
    permission_classes = [AllowAny]

    class StrictThrottle(UserRateThrottle):
        scope = "mock_strict"

        def get_rate(self):
            return "1/minute"

        def __init__(self):
            super().__init__()
            self.rate = self.get_rate()
            self.num_requests, self.duration = self.parse_rate(self.rate)

    throttle_classes = [StrictThrottle]

    def get(self, request):
        return Response({"status": "ok"})


class MockAIErrorView(APIView):
    """Test view that raises AI provider errors."""
    permission_classes = [AllowAny]

    def get(self, request):
        err_type = request.query_params.get("type")
        if err_type == "timeout":
            raise AITimeoutError("Gemini timed out.")
        if err_type == "config":
            raise AIConfigurationError("No API key.")
        raise AIProviderError("Gemini 500 error.")


@FAST_HASHERS_OVERRIDE
class CentralizedAPIErrorHandlingTests(TestCase):
    """
    Validates the centralized exception handler and API error consistency.
    """

    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.factory = APIRequestFactory()

        self.student = User.objects.create_user(
            username="test_student",
            email="student@example.com",
            password="TestPassword123!",
            role=User.Role.STUDENT,
        )
        self.instructor = User.objects.create_user(
            username="test_instructor",
            email="instructor@example.com",
            password="TestPassword123!",
            role=User.Role.INSTRUCTOR,
        )

    def tearDown(self):
        cache.clear()

    def _get_token(self, user):
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)

    # 1. Validation error -> 400
    def test_validation_error_returns_400_with_standard_format(self):
        response = self.client.post(
            "/api/auth/register/",
            {"username": "", "email": "invalid-email", "password": "short"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertEqual(response.data["error"]["code"], "validation_error")
        self.assertIn("message", response.data["error"])
        self.assertIn("details", response.data["error"])
        # Backward compatibility field checking
        self.assertIn("username", response.data)

    # 2. Unauthenticated -> 401
    def test_unauthenticated_returns_401_with_standard_format(self):
        response = self.client.get("/api/auth/me/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("error", response.data)
        self.assertEqual(response.data["error"]["code"], "not_authenticated")
        self.assertIn("Authentication credentials were not provided", response.data["error"]["message"])

    # 3. Authentication failed -> 401
    def test_authentication_failed_returns_401_with_standard_format(self):
        response = self.client.post(
            "/api/auth/token/",
            {"username": "test_student", "password": "WrongPassword123!"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("error", response.data)
        self.assertEqual(response.data["error"]["code"], "authentication_failed")

    # 4. Forbidden -> 403
    def test_forbidden_returns_403_with_standard_format(self):
        token = self._get_token(self.student)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = self.client.get("/api/instructor-test/")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("error", response.data)
        self.assertEqual(response.data["error"]["code"], "permission_denied")

    # 5. Not found -> 404
    def test_not_found_returns_404_with_standard_format(self):
        token = self._get_token(self.student)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = self.client.get("/api/courses/99999/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("error", response.data)
        self.assertEqual(response.data["error"]["code"], "not_found")

    # 6. Unsupported method -> 405
    def test_unsupported_method_returns_405_with_standard_format(self):
        response = self.client.patch("/api/auth/register/", {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertIn("error", response.data)
        self.assertEqual(response.data["error"]["code"], "method_not_allowed")

    # 7. Malformed JSON -> 400 (Parse error)
    def test_malformed_json_returns_400_parse_error(self):
        request = self.factory.post(
            "/api/auth/register/",
            data="{invalid_json:",
            content_type="application/json",
        )
        from accounts.views import RegisterView
        response = RegisterView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertEqual(response.data["error"]["code"], "parse_error")
        self.assertEqual(
            response.data["error"]["message"],
            "Malformed request body or invalid JSON.",
        )

    # 8. Throttled request -> 429
    def test_throttled_request_returns_429_with_standard_format(self):
        view = MockThrottledView.as_view()

        req1 = self.factory.get("/mock-throttle/")
        res1 = view(req1)
        self.assertEqual(res1.status_code, status.HTTP_200_OK)

        req2 = self.factory.get("/mock-throttle/")
        res2 = view(req2)
        self.assertEqual(res2.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertIn("error", res2.data)
        self.assertEqual(res2.data["error"]["code"], "rate_limited")
        self.assertIn("Retry-After", res2.headers)

    # 9. Unexpected exception -> 500 safe response
    def test_unexpected_server_error_returns_500_with_safe_response(self):
        view = MockCrashView.as_view()
        request = self.factory.get("/mock-crash/")
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn("error", response.data)
        self.assertEqual(response.data["error"]["code"], "server_error")
        self.assertEqual(
            response.data["error"]["message"],
            "An unexpected server error occurred.",
        )
        # Ensure secret and traceback are NOT leaked to client
        raw_output = str(response.data)
        self.assertNotIn("super_secret_password_999", raw_output)
        self.assertNotIn("Traceback", raw_output)
        self.assertNotIn("RuntimeError", raw_output)

    # 10. Unsupported media type -> 415
    def test_unsupported_media_type_returns_415_with_standard_format(self):
        view = MockMediaView.as_view()
        request = self.factory.post(
            "/mock-media/",
            data="<xml>test</xml>",
            content_type="text/xml",
        )
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)
        self.assertIn("error", response.data)
        self.assertEqual(response.data["error"]["code"], "unsupported_media_type")

    # 11. AI provider error -> 502
    def test_ai_provider_error_maps_to_502(self):
        view = MockAIErrorView.as_view()
        request = self.factory.get("/mock-ai/?type=provider")
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_502_BAD_GATEWAY)
        self.assertIn("error", response.data)
        self.assertEqual(response.data["error"]["code"], "provider_error")

    # 12. AI not configured -> 503
    def test_ai_not_configured_maps_to_503(self):
        view = MockAIErrorView.as_view()
        request = self.factory.get("/mock-ai/?type=config")
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertIn("error", response.data)
        self.assertEqual(response.data["error"]["code"], "ai_not_configured")

    # 13. AI timeout -> 504
    def test_ai_timeout_maps_to_504(self):
        view = MockAIErrorView.as_view()
        request = self.factory.get("/mock-ai/?type=timeout")
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_504_GATEWAY_TIMEOUT)
        self.assertIn("error", response.data)
        self.assertEqual(response.data["error"]["code"], "ai_timeout")

    # 14. Sensitive secrets never leaked in any error response
    def test_sensitive_secrets_shielded_from_client(self):
        endpoints = [
            ("/api/auth/register/", "POST", {"invalid": "data"}),
            ("/api/auth/token/", "POST", {"username": "x", "password": "y"}),
            ("/api/courses/99999/", "GET", None),
        ]
        sensitive_tokens = [
            getattr(settings, "SECRET_KEY", ""),
            getattr(settings, "DB_PASSWORD", ""),
            getattr(settings, "AI_API_KEY", ""),
        ]
        sensitive_tokens = [s for s in sensitive_tokens if s]

        for path, method, payload in endpoints:
            if method == "POST":
                resp = self.client.post(path, payload, format="json")
            else:
                resp = self.client.get(path)

            resp_str = str(resp.data)
            for secret in sensitive_tokens:
                self.assertNotIn(secret, resp_str)


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class AuthenticationAndRBACTests(TestCase):
    """
    Stage 17: Comprehensive testing for Authentication and Role-Based Access Control.
    """

    def setUp(self):
        cache.clear()
        self.client = APIClient()

        self.student = User.objects.create_user(
            username="auth_student",
            email="auth_student@example.com",
            password="StudentPassword123!",
            role=User.Role.STUDENT,
        )
        self.instructor = User.objects.create_user(
            username="auth_instructor",
            email="auth_instructor@example.com",
            password="InstructorPassword123!",
            role=User.Role.INSTRUCTOR,
        )
        self.admin = User.objects.create_user(
            username="auth_admin",
            email="auth_admin@example.com",
            password="AdminPassword123!",
            role=User.Role.ADMIN,
        )

    def _get_token(self, user):
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)

    # 1. Student registration
    def test_student_registration_success(self):
        payload = {
            "username": "new_student",
            "email": "new_student@example.com",
            "password": "ValidPassword123!",
        }
        response = self.client.post("/api/auth/register/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["username"], "new_student")
        self.assertEqual(response.data["email"], "new_student@example.com")
        self.assertNotIn("password", response.data)

        created_user = User.objects.get(username="new_student")
        self.assertEqual(created_user.role, User.Role.STUDENT)
        self.assertTrue(created_user.check_password("ValidPassword123!"))

    # 2. Instructor registration privilege protection
    def test_registration_ignores_role_escalation_attempt(self):
        payload = {
            "username": "escalation_user",
            "email": "escalation@example.com",
            "password": "ValidPassword123!",
            "role": "INSTRUCTOR",
        }
        response = self.client.post("/api/auth/register/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        created_user = User.objects.get(username="escalation_user")
        self.assertEqual(created_user.role, User.Role.STUDENT)

    def test_registration_ignores_admin_role_escalation_attempt(self):
        payload = {
            "username": "escalation_admin",
            "email": "escalation_admin@example.com",
            "password": "ValidPassword123!",
            "role": "ADMIN",
        }
        response = self.client.post("/api/auth/register/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        created_user = User.objects.get(username="escalation_admin")
        self.assertEqual(created_user.role, User.Role.STUDENT)

    # 3. Login success
    def test_login_success_returns_jwt_tokens(self):
        payload = {
            "username": "auth_student",
            "password": "StudentPassword123!",
        }
        response = self.client.post("/api/auth/token/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    # 4. Invalid login
    def test_login_invalid_password_fails(self):
        payload = {
            "username": "auth_student",
            "password": "WrongPassword123!",
        }
        response = self.client.post("/api/auth/token/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_nonexistent_user_fails(self):
        payload = {
            "username": "ghost_user",
            "password": "AnyPassword123!",
        }
        response = self.client.post("/api/auth/token/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # 5. JWT token refresh
    def test_jwt_token_refresh_lifecycle(self):
        refresh = RefreshToken.for_user(self.student)
        payload = {"refresh": str(refresh)}
        response = self.client.post("/api/auth/token/refresh/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_jwt_token_refresh_with_invalid_token_fails(self):
        payload = {"refresh": "invalid.refresh.token"}
        response = self.client.post("/api/auth/token/refresh/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # 6. /auth/me authorization
    def test_current_user_me_authenticated(self):
        token = self._get_token(self.student)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = self.client.get("/api/auth/me/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.student.id)
        self.assertEqual(response.data["username"], "auth_student")
        self.assertEqual(response.data["email"], "auth_student@example.com")
        self.assertEqual(response.data["role"], User.Role.STUDENT)

    # 7. Unauthenticated protected endpoint
    def test_current_user_me_unauthenticated_fails(self):
        response = self.client.get("/api/auth/me/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # 8. Invalid/expired token behavior
    def test_invalid_bearer_token_fails(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer garbage_token_xyz")
        response = self.client.get("/api/auth/me/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # 9. Student role behavior
    def test_student_role_authorization_matrix(self):
        token = self._get_token(self.student)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        self.assertEqual(self.client.get("/api/student-test/").status_code, status.HTTP_200_OK)
        self.assertEqual(self.client.get("/api/instructor-test/").status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.client.get("/api/admin-test/").status_code, status.HTTP_403_FORBIDDEN)

    # 10. Instructor role behavior
    def test_instructor_role_authorization_matrix(self):
        token = self._get_token(self.instructor)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        self.assertEqual(self.client.get("/api/instructor-test/").status_code, status.HTTP_200_OK)
        self.assertEqual(self.client.get("/api/student-test/").status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.client.get("/api/admin-test/").status_code, status.HTTP_403_FORBIDDEN)

    # 11. Admin role behavior
    def test_admin_role_authorization_matrix(self):
        token = self._get_token(self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        self.assertEqual(self.client.get("/api/admin-test/").status_code, status.HTTP_200_OK)
        self.assertEqual(self.client.get("/api/student-test/").status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.client.get("/api/instructor-test/").status_code, status.HTTP_403_FORBIDDEN)

    # 12. Stage 18 Security: Password validation on registration
    def test_registration_rejects_common_and_numeric_passwords(self):
        payload_numeric = {
            "username": "weak_numeric_user",
            "email": "weak_numeric@example.com",
            "password": "12345678",
        }
        res_numeric = self.client.post("/api/auth/register/", payload_numeric, format="json")
        self.assertEqual(res_numeric.status_code, status.HTTP_400_BAD_REQUEST)

        payload_common = {
            "username": "weak_common_user",
            "email": "weak_common@example.com",
            "password": "password",
        }
        res_common = self.client.post("/api/auth/register/", payload_common, format="json")
        self.assertEqual(res_common.status_code, status.HTTP_400_BAD_REQUEST)

    def test_registration_rejects_too_short_passwords(self):
        payload_short = {
            "username": "short_pw_user",
            "email": "short_pw@example.com",
            "password": "short",
        }
        res_short = self.client.post("/api/auth/register/", payload_short, format="json")
        self.assertEqual(res_short.status_code, status.HTTP_400_BAD_REQUEST)
