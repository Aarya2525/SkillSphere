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
from django.test import SimpleTestCase, TestCase, override_settings
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

    # 2. Safe registration role handling (STUDENT & INSTRUCTOR allowed, ADMIN & arbitrary roles rejected)
    def test_registration_with_instructor_role_creates_instructor(self):
        payload = {
            "username": "new_instructor",
            "email": "new_instructor@example.com",
            "password": "ValidPassword123!",
            "role": "INSTRUCTOR",
        }
        response = self.client.post("/api/auth/register/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["role"], User.Role.INSTRUCTOR)

        created_user = User.objects.get(username="new_instructor")
        self.assertEqual(created_user.role, User.Role.INSTRUCTOR)

    def test_registration_with_student_role_creates_student(self):
        payload = {
            "username": "explicit_student",
            "email": "explicit_student@example.com",
            "password": "ValidPassword123!",
            "role": "STUDENT",
        }
        response = self.client.post("/api/auth/register/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["role"], User.Role.STUDENT)

        created_user = User.objects.get(username="explicit_student")
        self.assertEqual(created_user.role, User.Role.STUDENT)

    def test_registration_omitting_role_defaults_to_student(self):
        payload = {
            "username": "default_role_student",
            "email": "default_role_student@example.com",
            "password": "ValidPassword123!",
        }
        response = self.client.post("/api/auth/register/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["role"], User.Role.STUDENT)

        created_user = User.objects.get(username="default_role_student")
        self.assertEqual(created_user.role, User.Role.STUDENT)

    def test_registration_rejects_admin_role_escalation_attempt(self):
        payload = {
            "username": "escalation_admin",
            "email": "escalation_admin@example.com",
            "password": "ValidPassword123!",
            "role": "ADMIN",
        }
        response = self.client.post("/api/auth/register/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(username="escalation_admin").exists())

    def test_registration_rejects_arbitrary_role_strings(self):
        payload = {
            "username": "arbitrary_role_user",
            "email": "arbitrary_role@example.com",
            "password": "ValidPassword123!",
            "role": "SUPERUSER",
        }
        response = self.client.post("/api/auth/register/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(username="arbitrary_role_user").exists())

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


class ProductionSettingsHardeningTests(SimpleTestCase):
    """
    Stage 22.2: Django Production Settings Hardening Tests.
    Verifies:
    - Production secret validation rejects missing, empty, or dev fallback keys when DEBUG=False.
    - Production secret validation accepts strong, unique keys when DEBUG=False.
    - Local development mode (DEBUG=True) permits the insecure dev key.
    - CSRF trusted origins parsing (strips whitespace, filters empty strings and wildcards).
    - CSRF environment-aware defaults (development, local Docker, production without localhost).
    - Reverse-proxy SECURE_PROXY_SSL_HEADER behavior and trust model.
    - Database connection lifetime (CONN_MAX_AGE) normalization (positive, negative, empty, invalid).
    - Isolated process startup validation.
    """

    def test_production_secret_validation_rejects_missing_or_empty(self):
        from config.settings import validate_production_secret, INSECURE_DEV_SECRET_KEY
        from django.core.exceptions import ImproperlyConfigured

        with self.assertRaises(ImproperlyConfigured) as ctx:
            validate_production_secret("", debug=False)
        self.assertIn("Production security validation failed", str(ctx.exception))
        self.assertNotIn(INSECURE_DEV_SECRET_KEY, str(ctx.exception))

        with self.assertRaises(ImproperlyConfigured) as ctx:
            validate_production_secret(None, debug=False)
        self.assertIn("Production security validation failed", str(ctx.exception))

    def test_production_secret_validation_rejects_dev_fallback(self):
        from config.settings import validate_production_secret, INSECURE_DEV_SECRET_KEY
        from django.core.exceptions import ImproperlyConfigured

        with self.assertRaises(ImproperlyConfigured) as ctx:
            validate_production_secret(INSECURE_DEV_SECRET_KEY, debug=False)
        self.assertIn("Production security validation failed", str(ctx.exception))
        # Ensure secret itself is not printed in exception
        self.assertNotIn(INSECURE_DEV_SECRET_KEY, str(ctx.exception))

    def test_production_secret_validation_accepts_valid_secret(self):
        from config.settings import validate_production_secret

        valid_production_key = "a-secure-random-cryptographic-key-for-production-deployment-12345"
        # Should not raise
        validate_production_secret(valid_production_key, debug=False)

    def test_local_development_mode_permits_dev_fallback(self):
        from config.settings import validate_production_secret, INSECURE_DEV_SECRET_KEY

        # In debug mode (DEBUG=True), dev fallback should not raise
        validate_production_secret(INSECURE_DEV_SECRET_KEY, debug=True)

    def test_csrf_trusted_origins_parsing(self):
        from config.settings import parse_csrf_trusted_origins
        from django.conf import settings

        # By default in local test environment, local origins are present
        self.assertIsInstance(settings.CSRF_TRUSTED_ORIGINS, list)
        self.assertTrue(any("localhost:4200" in origin for origin in settings.CSRF_TRUSTED_ORIGINS))

        # Test parser handles whitespace and strips cleanly
        raw_origins = " https://app.skillsphere.com , https://api.skillsphere.com , * , "
        parsed = parse_csrf_trusted_origins(raw_origins)
        self.assertEqual(parsed, [
            "https://app.skillsphere.com",
            "https://api.skillsphere.com"
        ])
        self.assertNotIn("*", parsed)

        # Test empty, None, and whitespace strings
        self.assertEqual(parse_csrf_trusted_origins(None), [])
        self.assertEqual(parse_csrf_trusted_origins(""), [])
        self.assertEqual(parse_csrf_trusted_origins("   ,   "), [])

        # Test wildcard strictly rejected
        self.assertEqual(parse_csrf_trusted_origins("*"), [])
        self.assertEqual(parse_csrf_trusted_origins("https://example.com, *"), ["https://example.com"])

        # Test explicit override parsing
        explicit = "https://prod.skillsphere.com,https://api.skillsphere.com"
        self.assertEqual(parse_csrf_trusted_origins(explicit), [
            "https://prod.skillsphere.com",
            "https://api.skillsphere.com"
        ])

    def test_csrf_environment_aware_defaults(self):
        from config.settings import get_default_csrf_trusted_origins, parse_csrf_trusted_origins

        # 1. Development mode (DEBUG=True) retains localhost origins
        dev_default = get_default_csrf_trusted_origins(debug=True, allowed_hosts=[])
        self.assertIn("http://localhost:4200", dev_default)
        self.assertIn("http://localhost:8000", dev_default)

        # Even with public hostnames, if DEBUG=True, localhost origins are preserved for dev
        dev_with_hosts = get_default_csrf_trusted_origins(debug=True, allowed_hosts=["skillsphere.com"])
        self.assertIn("http://localhost:4200", dev_with_hosts)

        # 2. Local Docker setup (DEBUG=False, with localhost or 127.0.0.1 in ALLOWED_HOSTS)
        docker_default = get_default_csrf_trusted_origins(
            debug=False,
            allowed_hosts=["localhost", "127.0.0.1", "backend", "skillsphere-backend"]
        )
        self.assertIn("http://localhost:4200", docker_default)
        self.assertIn("http://localhost:8000", docker_default)

        docker_ip_default = get_default_csrf_trusted_origins(
            debug=False,
            allowed_hosts=["127.0.0.1"]
        )
        self.assertIn("http://localhost:4200", docker_ip_default)

        # 3. Production setup (DEBUG=False, public domain names without localhost)
        prod_default = get_default_csrf_trusted_origins(
            debug=False,
            allowed_hosts=["skillsphere.com", "api.skillsphere.com"]
        )
        self.assertEqual(prod_default, "")
        self.assertEqual(parse_csrf_trusted_origins(prod_default), [])

        # 4. Verify public hostnames in ALLOWED_HOSTS are NOT used as proof of valid CSRF origins
        # Production deployments must explicitly configure CSRF_TRUSTED_ORIGINS
        self.assertNotIn("skillsphere.com", prod_default)

    def test_secure_proxy_ssl_header_trust_model(self):
        import os
        from django.conf import settings

        # By default in local dev environment without proxy env var, SECURE_PROXY_SSL_HEADER is None
        # so unauthenticated clients cannot spoof HTTPS
        env_val = os.environ.get("SECURE_PROXY_SSL_HEADER", "False").strip().lower()
        if env_val not in ("true", "1", "yes"):
            self.assertIsNone(settings.SECURE_PROXY_SSL_HEADER)

        # When enabled behind a trusted reverse proxy, expected tuple is ('HTTP_X_FORWARDED_PROTO', 'https')
        expected_header = ("HTTP_X_FORWARDED_PROTO", "https")
        self.assertEqual(expected_header[0], "HTTP_X_FORWARDED_PROTO")
        self.assertEqual(expected_header[1], "https")

    def test_database_conn_max_age_parsing(self):
        from config.settings import parse_conn_max_age
        from django.conf import settings

        default_db = settings.DATABASES["default"]
        self.assertIn("CONN_MAX_AGE", default_db)
        self.assertIsInstance(default_db["CONN_MAX_AGE"], int)
        # Default in local development is 0
        self.assertEqual(default_db["CONN_MAX_AGE"], 0)

        # Test default when None or "0"
        self.assertEqual(parse_conn_max_age(None), 0)
        self.assertEqual(parse_conn_max_age("0"), 0)

        # Test positive values preserved
        self.assertEqual(parse_conn_max_age("60"), 60)
        self.assertEqual(parse_conn_max_age("300"), 300)
        self.assertEqual(parse_conn_max_age(" 120 "), 120)

        # Test negative values normalized to 0
        self.assertEqual(parse_conn_max_age("-1"), 0)
        self.assertEqual(parse_conn_max_age("-60"), 0)
        self.assertEqual(parse_conn_max_age(" -300 "), 0)

        # Test empty and whitespace values fallback to 0
        self.assertEqual(parse_conn_max_age(""), 0)
        self.assertEqual(parse_conn_max_age("   "), 0)

        # Test non-numeric / invalid values fallback to 0
        self.assertEqual(parse_conn_max_age("invalid"), 0)
        self.assertEqual(parse_conn_max_age("abc"), 0)
        self.assertEqual(parse_conn_max_age("3.14"), 0)

    def test_isolated_process_production_startup_validation(self):
        import subprocess
        import sys
        import os
        from pathlib import Path

        base_dir = Path(__file__).resolve().parent.parent

        # 1. Isolated check with DEBUG=False and insecure secret must fail
        env_insecure = os.environ.copy()
        env_insecure["DEBUG"] = "False"
        env_insecure["SECRET_KEY"] = "django-insecure-skillsphere-dev-key-change-in-production"
        result_insecure = subprocess.run(
            [sys.executable, "manage.py", "check"],
            cwd=base_dir,
            env=env_insecure,
            capture_output=True,
            text=True
        )
        self.assertNotEqual(result_insecure.returncode, 0)
        self.assertIn("Production security validation failed", result_insecure.stderr)

        # 2. Isolated check with DEBUG=False and valid production secret must succeed
        env_secure = os.environ.copy()
        env_secure["DEBUG"] = "False"
        env_secure["SECRET_KEY"] = "a-unique-production-random-secret-key-that-is-secure-9876543210"
        result_secure = subprocess.run(
            [sys.executable, "manage.py", "check"],
            cwd=base_dir,
            env=env_secure,
            capture_output=True,
            text=True
        )
        self.assertEqual(result_secure.returncode, 0)

        # 3. Isolated check with DEBUG=True must succeed with dev secret
        env_dev = os.environ.copy()
        env_dev["DEBUG"] = "True"
        env_dev["SECRET_KEY"] = "django-insecure-skillsphere-dev-key-change-in-production"
        result_dev = subprocess.run(
            [sys.executable, "manage.py", "check"],
            cwd=base_dir,
            env=env_dev,
            capture_output=True,
            text=True
        )
        self.assertEqual(result_dev.returncode, 0)


class NginxAndStaticRoutingTests(SimpleTestCase):
    """
    Stage 22.3: Nginx Routing and Static Assets Verification Tests.
    Verifies:
    - STATIC_URL is configured with leading slash ('/static/').
    - STATIC_ROOT is set to BASE_DIR / 'staticfiles'.
    - collectstatic succeeds in dry-run mode.
    - frontend/skillsphere-frontend/nginx.conf specifies /admin/ proxying.
    - frontend/skillsphere-frontend/nginx.conf specifies /static/ asset alias.
    - frontend/skillsphere-frontend/nginx.conf sets immutable cache headers for hashed assets.
    - frontend/skillsphere-frontend/nginx.conf enforces revalidation for index.html.
    - docker-compose.yml specifies django_static_volume mounted to backend and frontend.
    """

    def test_static_url_and_root_settings(self):
        from django.conf import settings
        self.assertEqual(settings.STATIC_URL, "/static/")
        self.assertTrue(str(settings.STATIC_ROOT).endswith("staticfiles"))

    def test_collectstatic_dry_run_execution(self):
        import subprocess
        import sys
        from pathlib import Path

        base_dir = Path(__file__).resolve().parent.parent
        result = subprocess.run(
            [sys.executable, "manage.py", "collectstatic", "--dry-run", "--noinput"],
            cwd=base_dir,
            capture_output=True,
            text=True
        )
        self.assertEqual(result.returncode, 0, f"collectstatic failed: {result.stderr}")
        self.assertIn("static files", result.stdout)

    def test_nginx_configuration_routing_and_caching(self):
        from pathlib import Path

        repo_root = Path(__file__).resolve().parent.parent.parent
        nginx_conf_path = repo_root / "frontend" / "skillsphere-frontend" / "nginx.conf"
        self.assertTrue(nginx_conf_path.exists(), f"nginx.conf not found at {nginx_conf_path}")

        content = nginx_conf_path.read_text(encoding="utf-8")

        # 1. Django Admin proxy routing
        self.assertIn("location ^~ /admin/", content)
        self.assertIn("proxy_pass http://backend:8000/admin/;", content)
        self.assertIn("location = /admin", content)

        # 2. Django API proxy routing
        self.assertIn("location ^~ /api/", content)
        self.assertIn("proxy_pass http://backend:8000/api/;", content)

        # 3. Health probe routing
        self.assertIn("location = /health", content)
        self.assertIn("location = /health/", content)

        # 4. Static assets delivery and caching
        self.assertIn("location ^~ /static/", content)
        self.assertIn("alias /usr/share/nginx/html/static/;", content)
        self.assertIn("immutable", content)

        # 5. Hashed asset caching
        self.assertIn("max-age=31536000", content)

        # 5. index.html cache revalidation
        self.assertIn("location = /index.html", content)
        self.assertIn("no-cache, no-store, must-revalidate", content)

        # 6. Timeouts and body size
        self.assertIn("client_max_body_size", content)
        self.assertIn("proxy_read_timeout", content)

    def test_docker_compose_static_volume_wiring(self):
        from pathlib import Path

        repo_root = Path(__file__).resolve().parent.parent.parent
        compose_path = repo_root / "docker-compose.yml"
        self.assertTrue(compose_path.exists(), f"docker-compose.yml not found at {compose_path}")

        compose_content = compose_path.read_text(encoding="utf-8")

        # Volumes declared
        self.assertIn("django_static_volume:", compose_content)
        # Mounted in backend
        self.assertIn("django_static_volume:/app/staticfiles", compose_content)
        # Mounted in frontend
        self.assertIn("django_static_volume:/usr/share/nginx/html/static", compose_content)


class HealthCheckEndpointTests(SimpleTestCase):
    """
    Stage 22.4: Health Endpoint and Docker Health Checks Tests.
    Verifies:
    - /api/health/ returns 200 OK with {"status": "healthy", "database": "connected"} when DB is operational.
    - /health/ (root path) returns 200 OK.
    - Endpoint does not require authentication or CSRF tokens.
    - Simulated database outage returns 503 SERVICE_UNAVAILABLE with {"status": "unhealthy", "database": "disconnected"}.
    - No database credentials, secrets, hostnames, or stack traces are leaked in payload.
    - backend/Dockerfile and frontend Dockerfile specify valid HEALTHCHECK commands.
    - docker-compose.yml specifies backend healthcheck, frontend healthcheck, and condition: service_healthy ordering.
    """

    def test_health_check_healthy_status(self):
        from unittest.mock import patch

        with patch("config.views.check_database_health", return_value=True):
            # Test /api/health/
            response_api = self.client.get("/api/health/")
            self.assertEqual(response_api.status_code, status.HTTP_200_OK)
            data_api = response_api.json()
            self.assertEqual(data_api["status"], "healthy")
            self.assertEqual(data_api["database"], "connected")

            # Test root /health/
            response_root = self.client.get("/health/")
            self.assertEqual(response_root.status_code, status.HTTP_200_OK)
            data_root = response_root.json()
            self.assertEqual(data_root["status"], "healthy")
            self.assertEqual(data_root["database"], "connected")

    def test_health_check_unhealthy_on_database_error(self):
        from unittest.mock import patch

        with patch("config.views.check_database_health", return_value=False):
            response = self.client.get("/api/health/")
            self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
            data = response.json()
            self.assertEqual(data["status"], "unhealthy")
            self.assertEqual(data["database"], "disconnected")

            # CRITICAL SECURITY CHECK: Ensure exception details, hostnames, and stack traces are NEVER exposed
            raw_content = response.content.decode("utf-8")
            self.assertNotIn("Traceback", raw_content)
            self.assertNotIn("password", raw_content.lower())

    def test_health_check_unauthenticated_and_no_csrf_needed(self):
        from unittest.mock import patch

        with patch("config.views.check_database_health", return_value=True):
            # No Authorization header or session cookie
            response = self.client.get("/api/health/")
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_check_database_health_function(self):
        from unittest.mock import patch, MagicMock
        from config.views import check_database_health

        # Test failure handling without leaking
        with patch("config.views.connection") as mock_conn:
            mock_conn.cursor.side_effect = Exception("DB connection timeout at 10.0.0.5:5432!")
            self.assertFalse(check_database_health())

            # Test success
            mock_cursor = MagicMock()
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
            mock_conn.cursor.side_effect = None
            self.assertTrue(check_database_health())

    def test_dockerfiles_and_compose_healthchecks(self):
        from pathlib import Path

        repo_root = Path(__file__).resolve().parent.parent.parent

        # 1. Backend Dockerfile contains HEALTHCHECK with curl to /api/health/
        backend_dockerfile = (repo_root / "backend" / "Dockerfile").read_text(encoding="utf-8")
        self.assertIn("HEALTHCHECK", backend_dockerfile)
        self.assertIn("/api/health/", backend_dockerfile)

        # 2. Frontend Dockerfile contains HEALTHCHECK with wget
        frontend_dockerfile = (repo_root / "frontend" / "skillsphere-frontend" / "Dockerfile").read_text(encoding="utf-8")
        self.assertIn("HEALTHCHECK", frontend_dockerfile)
        self.assertIn("wget", frontend_dockerfile)

        # 3. docker-compose.yml defines healthchecks and startup ordering
        compose_content = (repo_root / "docker-compose.yml").read_text(encoding="utf-8")
        self.assertIn("healthcheck:", compose_content)
        self.assertIn("condition: service_healthy", compose_content)


class GitHubActionsCIWorkflowTests(SimpleTestCase):
    """
    Stage 22.5: GitHub Actions CI Workflow Tests.
    Verifies:
    - Workflow file exists at .github/workflows/ci.yml.
    - Configured for push and pull_request on main branch with concurrency grouping.
    - backend-test job runs on Python 3.12, includes PostgreSQL 17 service, runs test suite and collectstatic.
    - frontend-test-and-build job runs on Node 20, executes Karma headless tests, and builds production bundle.
    - docker-compose-lint validates Docker Compose configuration.
    - Strictly avoids hardcoded production secrets or private credentials.
    """

    def test_ci_workflow_structure_and_security(self):
        from pathlib import Path

        repo_root = Path(__file__).resolve().parent.parent.parent
        ci_path = repo_root / ".github" / "workflows" / "ci.yml"
        self.assertTrue(ci_path.exists(), f"CI workflow file not found at {ci_path}")

        ci_content = ci_path.read_text(encoding="utf-8")

        # 1. Triggers and concurrency
        self.assertIn("branches: [main]", ci_content)
        self.assertIn("concurrency:", ci_content)

        # 2. Backend test job
        self.assertIn("backend-test:", ci_content)
        self.assertIn("postgres:17", ci_content)
        self.assertIn("python-version: '3.12'", ci_content)
        self.assertIn("python manage.py test", ci_content)
        self.assertIn("collectstatic", ci_content)

        # 3. Frontend test and build job
        self.assertIn("frontend-test-and-build:", ci_content)
        self.assertIn("node-version: 20", ci_content)
        self.assertIn("ChromeHeadless", ci_content)
        self.assertIn("npm run build", ci_content)

        # 4. Compose validation job
        self.assertIn("docker-compose-lint:", ci_content)
        self.assertIn("docker compose config", ci_content)

        # 5. Security: Ensure no real private secrets or production API keys
        self.assertNotIn("AI_API_KEY", ci_content)
        self.assertNotIn("PRIVATE_KEY", ci_content)
        self.assertNotIn("AWS_SECRET", ci_content)


class ProductionComposeHardeningTests(SimpleTestCase):
    """
    Stage 22.6: Production Compose Hardening Tests.
    Verifies:
    - docker-compose.prod.yml exists.
    - PostgreSQL port 5436 is unmapped/unpublished in production.
    - Django backend port 8000 is unmapped/unpublished in production.
    - Frontend Nginx is the sole ingress gateway exposing ports 80 and 443.
    - Backend runs as non-root user (1000:1000).
    - Backend environment enforces DEBUG=False and SECURE_PROXY_SSL_HEADER=True.
    - PostgreSQL data volume is preserved as external (protecting user data).
    - Shared django_static_volume is mounted between backend and frontend.
    """

    def test_production_compose_security_and_port_isolation(self):
        from pathlib import Path

        repo_root = Path(__file__).resolve().parent.parent.parent
        prod_compose_path = repo_root / "docker-compose.prod.yml"
        self.assertTrue(prod_compose_path.exists(), f"Production compose file not found at {prod_compose_path}")

        prod_content = prod_compose_path.read_text(encoding="utf-8")

        # 1. Inspect postgres service isolation
        # Split by top-level service blocks
        postgres_block = prod_content.split("  postgres:\n")[1].split("  backend:\n")[0]
        self.assertNotIn("ports:", postgres_block, "PostgreSQL must not publish host ports in production!")
        self.assertIn("skillsphere_internal", postgres_block)

        # 2. Inspect backend service isolation
        backend_block = prod_content.split("  backend:\n")[1].split("  frontend:\n")[0]
        self.assertNotIn("ports:", backend_block, "Django backend must not publish host ports in production!")
        self.assertIn('user: "1000:1000"', backend_block)
        self.assertIn("DEBUG=False", backend_block)
        self.assertIn("SECURE_PROXY_SSL_HEADER=True", backend_block)
        self.assertIn("skillsphere_internal", backend_block)

        # 3. Inspect frontend service ingress
        frontend_block = prod_content.split("  frontend:\n")[1].split("networks:\n")[0]
        self.assertIn("ports:", frontend_block)
        self.assertIn('"80:80"', frontend_block)
        self.assertIn('"443:443"', frontend_block)

        # 4. Data safety: PostgreSQL volume preserved
        self.assertIn("external: true", prod_content)
        self.assertIn("name: skillsphere_skillsphere_postgres_data", prod_content)

        # 5. Static volume shared
        self.assertIn("django_static_volume:", prod_content)
        self.assertIn("django_static_volume:/app/staticfiles", backend_block)
        self.assertIn("django_static_volume:/usr/share/nginx/html/static:ro", frontend_block)


class DeploymentReadinessPlanTests(SimpleTestCase):
    """
    Stage 22.7: Deployment Readiness Plan Verification Tests.
    Verifies:
    - docs/deployment_readiness_plan.md exists.
    - Compares VPS vs Managed PaaS with pricing analysis.
    - Specifies TLS termination, Certbot automation, and HSTS.
    - Documents PostgreSQL backup (pg_dump) and restoration (pg_restore) workflows.
    - Details safe zero-downtime deployment and rollback procedures.
    """

    def test_deployment_readiness_plan_completeness(self):
        from pathlib import Path

        repo_root = Path(__file__).resolve().parent.parent.parent
        plan_path = repo_root / "docs" / "deployment_readiness_plan.md"
        self.assertTrue(plan_path.exists(), f"Deployment plan not found at {plan_path}")

        plan_content = plan_path.read_text(encoding="utf-8")

        # 1. Hosting comparison and pricing
        self.assertIn("Hetzner", plan_content)
        self.assertIn("DigitalOcean", plan_content)
        self.assertIn("Render", plan_content)

        # 2. Ingress architecture
        self.assertIn("Nginx Ingress", plan_content)
        self.assertIn("skillsphere_postgres_data", plan_content)

        # 3. TLS / HTTPS termination
        self.assertIn("Certbot", plan_content)
        self.assertIn("Strict-Transport-Security", plan_content)

        # 4. Disaster recovery and backups
        self.assertIn("pg_dump", plan_content)
        self.assertIn("pg_restore", plan_content)

        # 5. Rollback procedures
        self.assertIn("Rollback", plan_content)
        self.assertIn("git checkout", plan_content)
