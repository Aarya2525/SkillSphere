"""
Stage 17: Comprehensive testing for Certificates.
Covers prerequisite checks (100% lessons + quiz pass), UUID verification code,
public verification, access isolation, duplicate prevention, and notifications.
"""
import uuid
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from rest_framework import status
from rest_framework.test import APITestCase

from test_utils.base import FAST_HASHERS_OVERRIDE
from certificates.models import Certificate
from courses.models import Course, Module, Lesson
from enrollments.models import Enrollment
from learning.models import LessonProgress
from notifications.models import Notification
from quizzes.models import Quiz, Question, Option, QuizAttempt

User = get_user_model()


@FAST_HASHERS_OVERRIDE
class CertificateLifecycleTests(APITestCase):

    def setUp(self):
        self.instructor = User.objects.create_user(
            username="cert_inst",
            email="cert_inst@example.com",
            password="password123",
            role=User.Role.INSTRUCTOR,
        )
        self.student1 = User.objects.create_user(
            username="cert_student1",
            email="cert_student1@example.com",
            password="password123",
            role=User.Role.STUDENT,
        )
        self.student2 = User.objects.create_user(
            username="cert_student2",
            email="cert_student2@example.com",
            password="password123",
            role=User.Role.STUDENT,
        )
        self.admin = User.objects.create_user(
            username="cert_admin",
            email="cert_admin@example.com",
            password="password123",
            role=User.Role.ADMIN,
        )

        # Course with 2 lessons
        self.course = Course.objects.create(
            instructor=self.instructor,
            title="Certificate Masterclass",
            is_published=True,
        )
        self.module = Module.objects.create(
            course=self.course,
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

        # Quiz for course
        self.quiz = Quiz.objects.create(
            course=self.course,
            title="Final Assessment",
            passing_score=70,
            is_published=True,
        )
        self.question = Question.objects.create(quiz=self.quiz, text="What is 10 * 10?")
        self.opt_correct = Option.objects.create(question=self.question, text="100", is_correct=True)
        self.opt_wrong = Option.objects.create(question=self.question, text="99", is_correct=False)

        # Enroll student 1
        Enrollment.objects.create(student=self.student1, course=self.course)

    # 1. Premature generation: no lessons completed -> 400
    def test_certificate_fails_when_no_lessons_completed(self):
        self.client.force_authenticate(user=self.student1)
        response = self.client.post("/api/certificates/", {"course": self.course.id})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("not completed", str(response.data).lower())

    # 2. Premature generation: partially completed lessons (50%) -> 400
    def test_certificate_fails_when_lessons_partially_completed(self):
        LessonProgress.objects.create(student=self.student1, lesson=self.lesson1, is_completed=True)
        self.client.force_authenticate(user=self.student1)
        response = self.client.post("/api/certificates/", {"course": self.course.id})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("not completed", str(response.data).lower())

    # 3. Premature generation: 100% lessons completed but quiz NOT passed -> 400
    def test_certificate_fails_when_quiz_not_passed(self):
        LessonProgress.objects.create(student=self.student1, lesson=self.lesson1, is_completed=True)
        LessonProgress.objects.create(student=self.student1, lesson=self.lesson2, is_completed=True)
        self.client.force_authenticate(user=self.student1)
        response = self.client.post("/api/certificates/", {"course": self.course.id})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("pass the course assessment quiz", str(response.data).lower())

    # 4. Successful certificate generation after passing all requirements
    def test_certificate_generation_success_lifecycle(self):
        # Complete all lessons
        LessonProgress.objects.create(student=self.student1, lesson=self.lesson1, is_completed=True)
        LessonProgress.objects.create(student=self.student1, lesson=self.lesson2, is_completed=True)

        # Pass quiz
        QuizAttempt.objects.create(
            student=self.student1,
            quiz=self.quiz,
            score=1,
            total_questions=1,
            percentage=100,
            is_passed=True,
        )

        self.client.force_authenticate(user=self.student1)
        response = self.client.post("/api/certificates/", {"course": self.course.id})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("certificate", response.data)
        cert_data = response.data["certificate"]
        self.assertEqual(cert_data["student"], self.student1.id)
        self.assertEqual(cert_data["course"], self.course.id)
        self.assertEqual(cert_data["completion_percentage"], 100)
        self.assertIn("certificate_id", cert_data)

        # Verify notification created
        notif = Notification.objects.filter(
            recipient=self.student1,
            notification_type="CERTIFICATE",
        ).first()
        self.assertIsNotNone(notif)
        self.assertIn(self.course.title, notif.message)

    # 5. Duplicate certificate returns existing (idempotent 200)
    def test_duplicate_certificate_returns_existing(self):
        LessonProgress.objects.create(student=self.student1, lesson=self.lesson1, is_completed=True)
        LessonProgress.objects.create(student=self.student1, lesson=self.lesson2, is_completed=True)
        QuizAttempt.objects.create(
            student=self.student1,
            quiz=self.quiz,
            score=1,
            total_questions=1,
            percentage=100,
            is_passed=True,
        )
        self.client.force_authenticate(user=self.student1)
        resp1 = self.client.post("/api/certificates/", {"course": self.course.id})
        self.assertEqual(resp1.status_code, status.HTTP_201_CREATED)

        # Second call
        resp2 = self.client.post("/api/certificates/", {"course": self.course.id})
        self.assertEqual(resp2.status_code, status.HTTP_200_OK)
        self.assertIn("already exists", str(resp2.data).lower())

    # 6. Unenrolled student cannot generate certificate -> 403
    def test_unenrolled_student_cannot_generate_certificate(self):
        self.client.force_authenticate(user=self.student2)
        response = self.client.post("/api/certificates/", {"course": self.course.id})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # 7. Non-student cannot generate certificate -> 403
    def test_instructor_cannot_generate_certificate(self):
        self.client.force_authenticate(user=self.instructor)
        response = self.client.post("/api/certificates/", {"course": self.course.id})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # 8. Public certificate verification endpoint works without auth
    def test_public_certificate_verification(self):
        cert = Certificate.objects.create(
            student=self.student1,
            course=self.course,
            completion_percentage=100,
        )
        # Unauthenticated client
        self.client.logout()
        response = self.client.get(f"/api/certificates/verify/{cert.certificate_id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["student_name"], self.student1.username)
        self.assertEqual(response.data["course_title"], self.course.title)

    # 9. Invalid certificate UUID returns 404
    def test_invalid_certificate_uuid_returns_404(self):
        random_uuid = uuid.uuid4()
        response = self.client.get(f"/api/certificates/verify/{random_uuid}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # 10. Student isolation: student2 cannot view student1's certificate
    def test_student_cannot_view_another_students_certificate(self):
        cert = Certificate.objects.create(
            student=self.student1,
            course=self.course,
            completion_percentage=100,
        )
        self.client.force_authenticate(user=self.student2)
        response = self.client.get(f"/api/certificates/{cert.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # 11. Database UniqueConstraint on (student, course)
    def test_database_unique_constraint_on_certificate(self):
        Certificate.objects.create(student=self.student1, course=self.course, completion_percentage=100)
        with self.assertRaises(IntegrityError):
            Certificate.objects.create(student=self.student1, course=self.course, completion_percentage=100)
