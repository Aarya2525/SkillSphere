"""
Stage 17: Comprehensive testing for Enrollments.
Covers student enrollment lifecycle, duplicate prevention, unpublished course restrictions,
role validation, notifications, scoping isolation, and database unique constraints.
"""
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from rest_framework import status
from rest_framework.test import APITestCase

from test_utils.base import FAST_HASHERS_OVERRIDE
from courses.models import Course
from enrollments.models import Enrollment
from notifications.models import Notification

User = get_user_model()


@FAST_HASHERS_OVERRIDE
class EnrollmentLifecycleTests(APITestCase):

    def setUp(self):
        self.instructor = User.objects.create_user(
            username="enroll_inst",
            email="enroll_inst@example.com",
            password="password123",
            role=User.Role.INSTRUCTOR,
        )
        self.student1 = User.objects.create_user(
            username="enroll_student1",
            email="enroll_student1@example.com",
            password="password123",
            role=User.Role.STUDENT,
        )
        self.student2 = User.objects.create_user(
            username="enroll_student2",
            email="enroll_student2@example.com",
            password="password123",
            role=User.Role.STUDENT,
        )
        self.admin = User.objects.create_user(
            username="enroll_admin",
            email="enroll_admin@example.com",
            password="password123",
            role=User.Role.ADMIN,
        )

        self.published_course = Course.objects.create(
            instructor=self.instructor,
            title="Published Django Course",
            description="A published course.",
            is_published=True,
        )
        self.unpublished_course = Course.objects.create(
            instructor=self.instructor,
            title="Unpublished Draft Course",
            description="A draft course.",
            is_published=False,
        )

    # 1. Student enrolls in published course
    def test_student_enrolls_in_published_course_success(self):
        self.client.force_authenticate(user=self.student1)
        response = self.client.post("/api/enrollments/", {
            "course": self.published_course.id,
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["student"], self.student1.id)
        self.assertEqual(response.data["course"], self.published_course.id)
        self.assertIn("enrolled_at", response.data)

        # Confirm DB record
        self.assertTrue(
            Enrollment.objects.filter(
                student=self.student1,
                course=self.published_course,
            ).exists()
        )

    # 2. Duplicate enrollment rejected
    def test_duplicate_enrollment_rejected_with_400(self):
        Enrollment.objects.create(
            student=self.student1,
            course=self.published_course,
        )
        self.client.force_authenticate(user=self.student1)
        response = self.client.post("/api/enrollments/", {
            "course": self.published_course.id,
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        error_str = str(response.data).lower()
        self.assertIn("already enrolled", error_str)

    # 3. Student cannot enroll in unpublished course
    def test_student_cannot_enroll_in_unpublished_course(self):
        self.client.force_authenticate(user=self.student1)
        response = self.client.post("/api/enrollments/", {
            "course": self.unpublished_course.id,
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        error_str = str(response.data).lower()
        self.assertIn("published courses", error_str)

    # 4. Instructor cannot enroll
    def test_instructor_cannot_enroll_in_courses(self):
        self.client.force_authenticate(user=self.instructor)
        response = self.client.post("/api/enrollments/", {
            "course": self.published_course.id,
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        error_str = str(response.data).lower()
        self.assertIn("only students", error_str)

    # 5. Unauthenticated user cannot enroll
    def test_unauthenticated_user_cannot_enroll(self):
        response = self.client.post("/api/enrollments/", {
            "course": self.published_course.id,
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # 6. Enrollment creates notification
    def test_enrollment_triggers_notification(self):
        self.client.force_authenticate(user=self.student1)
        response = self.client.post("/api/enrollments/", {
            "course": self.published_course.id,
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        notification = Notification.objects.filter(
            recipient=self.student1,
            notification_type="ENROLLMENT",
        ).first()
        self.assertIsNotNone(notification)
        self.assertIn(self.published_course.title, notification.message)

    # 7. Ownership isolation for enrollments list
    def test_enrollment_list_scoping_and_isolation(self):
        # Enroll student1
        e1 = Enrollment.objects.create(student=self.student1, course=self.published_course)

        # Second course for student2
        course2 = Course.objects.create(
            instructor=self.instructor,
            title="Course 2",
            is_published=True,
        )
        e2 = Enrollment.objects.create(student=self.student2, course=course2)

        # Student 1 only sees e1
        self.client.force_authenticate(user=self.student1)
        resp1 = self.client.get("/api/enrollments/")
        self.assertEqual(resp1.status_code, status.HTTP_200_OK)
        ids1 = [item["id"] for item in resp1.data]
        self.assertIn(e1.id, ids1)
        self.assertNotIn(e2.id, ids1)

        # Student 2 only sees e2
        self.client.force_authenticate(user=self.student2)
        resp2 = self.client.get("/api/enrollments/")
        self.assertEqual(resp2.status_code, status.HTTP_200_OK)
        ids2 = [item["id"] for item in resp2.data]
        self.assertIn(e2.id, ids2)
        self.assertNotIn(e1.id, ids2)

        # Admin sees both
        self.client.force_authenticate(user=self.admin)
        resp_admin = self.client.get("/api/enrollments/")
        self.assertEqual(resp_admin.status_code, status.HTTP_200_OK)
        admin_ids = [item["id"] for item in resp_admin.data]
        self.assertIn(e1.id, admin_ids)
        self.assertIn(e2.id, admin_ids)

    # 8. Invalid course ID returns 400
    def test_invalid_course_id_returns_400(self):
        self.client.force_authenticate(user=self.student1)
        response = self.client.post("/api/enrollments/", {
            "course": 999999,
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # 9. Database UniqueConstraint prevents duplicate enrollment at DB level
    def test_database_unique_constraint_enforced(self):
        Enrollment.objects.create(student=self.student1, course=self.published_course)
        with self.assertRaises(IntegrityError):
            Enrollment.objects.create(student=self.student1, course=self.published_course)
