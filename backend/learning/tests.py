"""
Stage 17: Comprehensive testing for Learning & Progress tracking.
Covers lesson progress creation, completion timestamps, enrollment authorization,
unpublished course blocking, duplicate prevention, student isolation, and course completion.
"""
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from rest_framework import status
from rest_framework.test import APITestCase

from test_utils.base import FAST_HASHERS_OVERRIDE
from courses.models import Course, Module, Lesson
from enrollments.models import Enrollment
from learning.models import LessonProgress

User = get_user_model()


@FAST_HASHERS_OVERRIDE
class LearningProgressLifecycleTests(APITestCase):

    def setUp(self):
        self.instructor = User.objects.create_user(
            username="learn_inst",
            email="learn_inst@example.com",
            password="password123",
            role=User.Role.INSTRUCTOR,
        )
        self.student1 = User.objects.create_user(
            username="learn_student1",
            email="learn_student1@example.com",
            password="password123",
            role=User.Role.STUDENT,
        )
        self.student2 = User.objects.create_user(
            username="learn_student2",
            email="learn_student2@example.com",
            password="password123",
            role=User.Role.STUDENT,
        )
        self.admin = User.objects.create_user(
            username="learn_admin",
            email="learn_admin@example.com",
            password="password123",
            role=User.Role.ADMIN,
        )

        # Published course with 2 lessons
        self.published_course = Course.objects.create(
            instructor=self.instructor,
            title="Learning Test Course",
            is_published=True,
        )
        self.module = Module.objects.create(
            course=self.published_course,
            title="Module 1",
            order=1,
        )
        self.lesson1 = Lesson.objects.create(
            module=self.module,
            title="Lesson 1",
            content="Content 1",
            order=1,
        )
        self.lesson2 = Lesson.objects.create(
            module=self.module,
            title="Lesson 2",
            content="Content 2",
            order=2,
        )

        # Unpublished course
        self.unpublished_course = Course.objects.create(
            instructor=self.instructor,
            title="Draft Course",
            is_published=False,
        )
        self.unpub_module = Module.objects.create(
            course=self.unpublished_course,
            title="Draft Module",
            order=1,
        )
        self.unpub_lesson = Lesson.objects.create(
            module=self.unpub_module,
            title="Draft Lesson",
            content="Draft Content",
            order=1,
        )

        # Enroll student 1 in published course
        Enrollment.objects.create(
            student=self.student1,
            course=self.published_course,
        )

    # 1. Enrolled student creates progress (incomplete)
    def test_enrolled_student_creates_progress(self):
        self.client.force_authenticate(user=self.student1)
        response = self.client.post("/api/learning/progress/", {
            "lesson": self.lesson1.id,
            "is_completed": False,
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["lesson"], self.lesson1.id)
        self.assertFalse(response.data["is_completed"])
        self.assertIsNone(response.data["completed_at"])

    # 2. Enrolled student marks lesson as completed
    def test_enrolled_student_marks_lesson_completed_sets_timestamp(self):
        self.client.force_authenticate(user=self.student1)
        response = self.client.post("/api/learning/progress/", {
            "lesson": self.lesson1.id,
            "is_completed": True,
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["is_completed"])
        self.assertIsNotNone(response.data["completed_at"])

    # 3. Non-enrolled student cannot create progress
    def test_non_enrolled_student_cannot_create_progress(self):
        self.client.force_authenticate(user=self.student2)
        response = self.client.post("/api/learning/progress/", {
            "lesson": self.lesson1.id,
            "is_completed": True,
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        error_str = str(response.data).lower()
        self.assertIn("must be enrolled", error_str)

    # 4. Progress creation blocked for unpublished course lessons
    def test_progress_blocked_for_unpublished_course_lessons(self):
        # Even if enrolled in something else, student cannot access unpublished course lesson
        self.client.force_authenticate(user=self.student1)
        response = self.client.post("/api/learning/progress/", {
            "lesson": self.unpub_lesson.id,
            "is_completed": True,
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        error_str = str(response.data).lower()
        self.assertIn("published courses", error_str)

    # 5. Instructor cannot create progress
    def test_instructor_cannot_create_progress(self):
        self.client.force_authenticate(user=self.instructor)
        response = self.client.post("/api/learning/progress/", {
            "lesson": self.lesson1.id,
            "is_completed": True,
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        error_str = str(response.data).lower()
        self.assertIn("only students", error_str)

    # 6. Progress update lifecycle (complete -> incomplete -> complete)
    def test_progress_update_lifecycle(self):
        progress = LessonProgress.objects.create(
            student=self.student1,
            lesson=self.lesson1,
            is_completed=False,
        )
        self.client.force_authenticate(user=self.student1)

        # Mark complete
        patch1 = self.client.patch(f"/api/learning/progress/{progress.id}/", {
            "is_completed": True,
        })
        self.assertEqual(patch1.status_code, status.HTTP_200_OK)
        self.assertTrue(patch1.data["is_completed"])
        self.assertIsNotNone(patch1.data["completed_at"])

        # Mark incomplete
        patch2 = self.client.patch(f"/api/learning/progress/{progress.id}/", {
            "is_completed": False,
        })
        self.assertEqual(patch2.status_code, status.HTTP_200_OK)
        self.assertFalse(patch2.data["is_completed"])
        self.assertIsNone(patch2.data["completed_at"])

    # 7. Student isolation: student2 cannot view or edit student1's progress
    def test_student_progress_isolation(self):
        progress = LessonProgress.objects.create(
            student=self.student1,
            lesson=self.lesson1,
            is_completed=True,
        )
        self.client.force_authenticate(user=self.student2)

        # Detail -> 404
        self.assertEqual(
            self.client.get(f"/api/learning/progress/{progress.id}/").status_code,
            status.HTTP_404_NOT_FOUND,
        )

        # Update -> 404
        self.assertEqual(
            self.client.patch(f"/api/learning/progress/{progress.id}/", {"is_completed": False}).status_code,
            status.HTTP_404_NOT_FOUND,
        )

        # List -> does not contain progress.id
        resp = self.client.get("/api/learning/progress/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertNotIn(progress.id, [p["id"] for p in resp.data])

    # 8. Admin can access all progress records
    def test_admin_can_access_all_progress(self):
        progress = LessonProgress.objects.create(
            student=self.student1,
            lesson=self.lesson1,
            is_completed=True,
        )
        self.client.force_authenticate(user=self.admin)
        resp = self.client.get(f"/api/learning/progress/{progress.id}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    # 9. Invalid lesson ID returns 400
    def test_invalid_lesson_id_returns_400(self):
        self.client.force_authenticate(user=self.student1)
        response = self.client.post("/api/learning/progress/", {
            "lesson": 999999,
            "is_completed": True,
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # 10. Database unique constraint on (student, lesson)
    def test_database_unique_constraint_on_student_lesson(self):
        LessonProgress.objects.create(student=self.student1, lesson=self.lesson1, is_completed=True)
        with self.assertRaises(IntegrityError):
            LessonProgress.objects.create(student=self.student1, lesson=self.lesson1, is_completed=True)

    # 11. Course completion calculation logic
    def test_course_completion_calculation(self):
        # 1 of 2 lessons completed = 50%
        LessonProgress.objects.create(student=self.student1, lesson=self.lesson1, is_completed=True)
        total_lessons = Lesson.objects.filter(module__course=self.published_course).count()
        completed_lessons = LessonProgress.objects.filter(
            student=self.student1,
            lesson__module__course=self.published_course,
            is_completed=True,
        ).count()
        completion_pct = round((completed_lessons / total_lessons) * 100)
        self.assertEqual(completion_pct, 50)

        # 2 of 2 completed = 100%
        LessonProgress.objects.create(student=self.student1, lesson=self.lesson2, is_completed=True)
        completed_lessons = LessonProgress.objects.filter(
            student=self.student1,
            lesson__module__course=self.published_course,
            is_completed=True,
        ).count()
        completion_pct = round((completed_lessons / total_lessons) * 100)
        self.assertEqual(completion_pct, 100)
