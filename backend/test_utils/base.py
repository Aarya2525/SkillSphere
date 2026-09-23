"""
Reusable test utilities, factories, and base test cases for SkillSphere.
Strictly isolated to test execution via override_settings.
"""
from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.test import APITestCase, APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from courses.models import Course, Module, Lesson
from enrollments.models import Enrollment
from learning.models import LessonProgress
from quizzes.models import Quiz, Question, Option, QuizAttempt
from certificates.models import Certificate
from reviews.models import Review
from notifications.models import Notification

User = get_user_model()

FAST_HASHERS_OVERRIDE = override_settings(
    PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"]
)


@FAST_HASHERS_OVERRIDE
class SkillSphereAPITestCase(APITestCase):
    """
    Base API test case providing fast test-only password hashing,
    isolated client instances, and reusable authentication helpers.
    """

    def setUp(self):
        super().setUp()
        self.client = APIClient()

    def authenticate_as(self, user):
        """Forces DRF authentication as the specified user."""
        self.client.force_authenticate(user=user)

    def get_jwt_credentials(self, user):
        """Returns HTTP Authorization header dict with valid Bearer JWT."""
        refresh = RefreshToken.for_user(user)
        return {"HTTP_AUTHORIZATION": f"Bearer {refresh.access_token}"}

    def authenticate_jwt(self, user):
        """Sets Bearer JWT header directly on self.client."""
        creds = self.get_jwt_credentials(user)
        self.client.credentials(**creds)


def create_test_user(
    username: str,
    email: str = None,
    password: str = "TestPassword123!",
    role: str = User.Role.STUDENT,
) -> User:
    """Creates a user with the requested role."""
    if email is None:
        email = f"{username}@example.com"
    return User.objects.create_user(
        username=username,
        email=email,
        password=password,
        role=role,
    )


def create_test_course(
    instructor: User,
    title: str = "Test Course",
    description: str = "Test Course Description",
    is_published: bool = True,
) -> Course:
    return Course.objects.create(
        instructor=instructor,
        title=title,
        description=description,
        is_published=is_published,
    )


def create_test_module(
    course: Course,
    title: str = "Module 1",
    order: int = 1,
) -> Module:
    return Module.objects.create(
        course=course,
        title=title,
        order=order,
    )


def create_test_lesson(
    module: Module,
    title: str = "Lesson 1",
    content: str = "Lesson test content.",
    order: int = 1,
) -> Lesson:
    return Lesson.objects.create(
        module=module,
        title=title,
        content=content,
        order=order,
    )


def create_test_enrollment(
    student: User,
    course: Course,
) -> Enrollment:
    return Enrollment.objects.create(
        student=student,
        course=course,
    )
