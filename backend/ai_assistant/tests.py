"""
Tests for the AI Learning Assistant app.
Ensures RBAC, access control, prompt context formulation, and error handling.
"""
from unittest.mock import patch, MagicMock
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from courses.models import Course, Module, Lesson
from enrollments.models import Enrollment
from .providers.base import (
    AIConfigurationError,
    AIProviderError,
    AITimeoutError,
)

User = get_user_model()


class AIAssistantSecurityTests(TestCase):
    """
    Validates authentication, authorization, RBAC, and error resilience for the AI Learning Assistant.
    """

    def setUp(self):
        self.client = APIClient()

        # Users
        self.instructor = User.objects.create_user(
            username="instructor_alice",
            email="alice@example.com",
            password="TestPassword123!",
            role=User.Role.INSTRUCTOR,
        )
        self.other_instructor = User.objects.create_user(
            username="instructor_bob",
            email="bob@example.com",
            password="TestPassword123!",
            role=User.Role.INSTRUCTOR,
        )
        self.enrolled_student = User.objects.create_user(
            username="student_charlie",
            email="charlie@example.com",
            password="TestPassword123!",
            role=User.Role.STUDENT,
        )
        self.non_enrolled_student = User.objects.create_user(
            username="student_david",
            email="david@example.com",
            password="TestPassword123!",
            role=User.Role.STUDENT,
        )

        # Published Course hierarchy
        self.published_course = Course.objects.create(
            title="Django Architecture",
            description="Deep dive into Django patterns.",
            instructor=self.instructor,
            is_published=True,
        )
        self.module_1 = Module.objects.create(
            course=self.published_course,
            title="Views & Routing",
            order=1,
        )
        self.lesson_1 = Lesson.objects.create(
            module=self.module_1,
            title="Class Based Views",
            content="Class-based views provide an object-oriented way to handle requests.",
            order=1,
        )

        # Enroll charlie in published_course
        Enrollment.objects.create(
            student=self.enrolled_student,
            course=self.published_course,
        )

        # Unpublished Course hierarchy
        self.unpublished_course = Course.objects.create(
            title="Unreleased Advanced Course",
            description="Draft content.",
            instructor=self.instructor,
            is_published=False,
        )
        self.unpublished_module = Module.objects.create(
            course=self.unpublished_course,
            title="Draft Module",
            order=1,
        )
        self.unpublished_lesson = Lesson.objects.create(
            module=self.unpublished_module,
            title="Draft Lesson",
            content="Top secret unreleased content.",
            order=1,
        )
        # Charlie is enrolled in unpublished course too (e.g. from early draft)
        Enrollment.objects.create(
            student=self.enrolled_student,
            course=self.unpublished_course,
        )

        self.url = "/api/ai/ask/"

    def _authenticate(self, user):
        refresh = RefreshToken.for_user(user)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}"
        )

    # 1. Unauthenticated request
    @patch("ai_assistant.views.ask_tutor")
    def test_unauthenticated_request_rejected(self, mock_ask_tutor):
        response = self.client.post(
            self.url,
            {"lesson_id": self.lesson_1.id, "message": "Help me understand."},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        mock_ask_tutor.assert_not_called()

    # 2. Authenticated enrolled student succeeds
    @patch("ai_assistant.views.ask_tutor")
    def test_authenticated_enrolled_student_can_ask(self, mock_ask_tutor):
        mock_ask_tutor.return_value = "CBVs allow reusability through inheritance."
        self._authenticate(self.enrolled_student)

        payload = {
            "lesson_id": self.lesson_1.id,
            "message": "Can you explain CBVs?",
        }
        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["answer"],
            "CBVs allow reusability through inheritance.",
        )
        self.assertEqual(response.data["lesson_id"], self.lesson_1.id)
        mock_ask_tutor.assert_called_once_with(self.lesson_1, "Can you explain CBVs?")

    # 3. Non-enrolled student forbidden (provider not called)
    @patch("ai_assistant.views.ask_tutor")
    def test_non_enrolled_student_forbidden(self, mock_ask_tutor):
        self._authenticate(self.non_enrolled_student)

        payload = {
            "lesson_id": self.lesson_1.id,
            "message": "Tell me about this lesson.",
        }
        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("error", response.data)
        mock_ask_tutor.assert_not_called()

    # 4. Enrolled student on unpublished course forbidden
    @patch("ai_assistant.views.ask_tutor")
    def test_unpublished_course_student_forbidden(self, mock_ask_tutor):
        self._authenticate(self.enrolled_student)

        payload = {
            "lesson_id": self.unpublished_lesson.id,
            "message": "Sneak peek please.",
        }
        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("error", response.data)
        mock_ask_tutor.assert_not_called()

    # 5. Non-existent lesson returns 404
    @patch("ai_assistant.views.ask_tutor")
    def test_nonexistent_lesson_returns_404(self, mock_ask_tutor):
        self._authenticate(self.enrolled_student)

        payload = {
            "lesson_id": 99999,
            "message": "Explain lesson 99999.",
        }
        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("error", response.data)
        mock_ask_tutor.assert_not_called()

    # 6. Invalid payload validation
    @patch("ai_assistant.views.ask_tutor")
    def test_invalid_payload_returns_400(self, mock_ask_tutor):
        self._authenticate(self.enrolled_student)

        # Missing message
        response = self.client.post(
            self.url,
            {"lesson_id": self.lesson_1.id},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Empty message
        response = self.client.post(
            self.url,
            {"lesson_id": self.lesson_1.id, "message": "   "},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        mock_ask_tutor.assert_not_called()

    # 7. AI provider configuration error returns 503
    @patch("ai_assistant.views.ask_tutor")
    def test_missing_ai_configuration_returns_503(self, mock_ask_tutor):
        mock_ask_tutor.side_effect = AIConfigurationError("Key not configured.")
        self._authenticate(self.enrolled_student)

        payload = {
            "lesson_id": self.lesson_1.id,
            "message": "Explain CBVs.",
        }
        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertIn("error", response.data)

    # 8. AI provider timeout returns 504
    @patch("ai_assistant.views.ask_tutor")
    def test_ai_provider_timeout_returns_504(self, mock_ask_tutor):
        mock_ask_tutor.side_effect = AITimeoutError("Timed out.")
        self._authenticate(self.enrolled_student)

        payload = {
            "lesson_id": self.lesson_1.id,
            "message": "Explain CBVs.",
        }
        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_504_GATEWAY_TIMEOUT)
        self.assertIn("error", response.data)

    # 9. AI provider error returns 502
    @patch("ai_assistant.views.ask_tutor")
    def test_ai_provider_error_returns_502(self, mock_ask_tutor):
        mock_ask_tutor.side_effect = AIProviderError("Upstream API error.")
        self._authenticate(self.enrolled_student)

        payload = {
            "lesson_id": self.lesson_1.id,
            "message": "Explain CBVs.",
        }
        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_502_BAD_GATEWAY)
        self.assertIn("error", response.data)

    # 10. Instructor can access their own course lesson
    @patch("ai_assistant.views.ask_tutor")
    def test_instructor_access_to_own_course(self, mock_ask_tutor):
        mock_ask_tutor.return_value = "Instructor preview response."
        self._authenticate(self.instructor)

        payload = {
            "lesson_id": self.lesson_1.id,
            "message": "Check my lesson.",
        }
        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_ask_tutor.assert_called_once()

    # 11. Instructor cannot access another instructor's course lesson
    @patch("ai_assistant.views.ask_tutor")
    def test_instructor_cannot_access_other_course(self, mock_ask_tutor):
        self._authenticate(self.other_instructor)

        payload = {
            "lesson_id": self.lesson_1.id,
            "message": "Spy on course.",
        }
        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("error", response.data)
        mock_ask_tutor.assert_not_called()
