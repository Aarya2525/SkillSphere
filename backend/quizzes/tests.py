from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from courses.models import Course, Module, Lesson
from enrollments.models import Enrollment
from learning.models import LessonProgress
from quizzes.models import Quiz, Question, Option, QuizAttempt

User = get_user_model()


class QuizSystemTests(APITestCase):

    def setUp(self):
        # Create users
        self.instructor1 = User.objects.create_user(
            username="instructor1",
            email="inst1@example.com",
            password="password123",
            role=User.Role.INSTRUCTOR
        )
        self.instructor2 = User.objects.create_user(
            username="instructor2",
            email="inst2@example.com",
            password="password123",
            role=User.Role.INSTRUCTOR
        )
        self.student = User.objects.create_user(
            username="student1",
            email="student1@example.com",
            password="password123",
            role=User.Role.STUDENT
        )
        self.unauthorized_student = User.objects.create_user(
            username="student2",
            email="student2@example.com",
            password="password123",
            role=User.Role.STUDENT
        )

        # Create courses
        self.course1 = Course.objects.create(
            instructor=self.instructor1,
            title="Django Advanced",
            description="Deep dive into Django",
            is_published=True
        )
        self.module1 = Module.objects.create(
            course=self.course1,
            title="Module 1",
            order=1
        )
        self.lesson1 = Lesson.objects.create(
            module=self.module1,
            title="Lesson 1",
            content="Lesson content",
            order=1
        )

        self.course2 = Course.objects.create(
            instructor=self.instructor2,
            title="React Basics",
            description="Learn React",
            is_published=True
        )

        # Enroll student in course1
        Enrollment.objects.create(student=self.student, course=self.course1)

    def test_quiz_model_defaults(self):
        quiz = Quiz.objects.create(
            course=self.course1,
            title="Sample Quiz",
            passing_score=80
        )
        self.assertEqual(quiz.passing_score, 80)
        self.assertFalse(quiz.is_published)

    def test_instructor_can_create_quiz_for_own_course(self):
        self.client.force_authenticate(user=self.instructor1)
        response = self.client.post("/api/quizzes/", {
            "course": self.course1.id,
            "title": "Django Mastery Quiz",
            "description": "Test your mastery",
            "passing_score": 75
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["title"], "Django Mastery Quiz")
        self.assertEqual(response.data["passing_score"], 75)
        self.assertFalse(response.data["is_published"])

    def test_instructor_cannot_create_quiz_for_another_instructors_course(self):
        self.client.force_authenticate(user=self.instructor1)
        response = self.client.post("/api/quizzes/", {
            "course": self.course2.id,
            "title": "Hacked Quiz",
            "passing_score": 75
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_quiz_publishing_validation(self):
        self.client.force_authenticate(user=self.instructor1)

        # 1. Empty quiz cannot be published
        quiz = Quiz.objects.create(
            course=self.course1,
            title="Validation Quiz",
            passing_score=70
        )
        response = self.client.put(f"/api/quizzes/{quiz.id}/", {
            "course": self.course1.id,
            "title": "Validation Quiz",
            "is_published": True
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        error_msg = str(response.data)
        self.assertIn("at least one question", error_msg.lower())

        # 2. Question with < 2 options cannot be published
        q1 = Question.objects.create(quiz=quiz, text="What is Python?")
        Option.objects.create(question=q1, text="Programming language", is_correct=True)

        response = self.client.put(f"/api/quizzes/{quiz.id}/", {
            "course": self.course1.id,
            "title": "Validation Quiz",
            "is_published": True
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        error_msg = str(response.data)
        self.assertIn("at least 2 options", error_msg.lower())

        # 3. Question without correct option cannot be published
        Option.objects.create(question=q1, text="A snake only", is_correct=False)
        opt1 = q1.options.first()
        opt1.is_correct = False
        opt1.save()

        response = self.client.put(f"/api/quizzes/{quiz.id}/", {
            "course": self.course1.id,
            "title": "Validation Quiz",
            "is_published": True
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        error_msg = str(response.data)
        self.assertIn("exactly one correct option", error_msg.lower())

        # 4. Valid quiz successfully publishes
        opt1.is_correct = True
        opt1.save()

        response = self.client.put(f"/api/quizzes/{quiz.id}/", {
            "course": self.course1.id,
            "title": "Validation Quiz",
            "is_published": True
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["is_published"])

    def test_student_cannot_access_unpublished_quiz(self):
        quiz = Quiz.objects.create(
            course=self.course1,
            title="Unpublished Quiz",
            is_published=False
        )
        self.client.force_authenticate(user=self.student)
        response = self.client.get(f"/api/quizzes/student/{quiz.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_student_cannot_access_quiz_for_unenrolled_course(self):
        quiz = Quiz.objects.create(
            course=self.course2,
            title="React Quiz",
            is_published=True
        )
        self.client.force_authenticate(user=self.student)
        response = self.client.get(f"/api/quizzes/student/{quiz.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_quiz_submission_and_server_side_scoring(self):
        # Set up a published quiz with 2 questions
        quiz = Quiz.objects.create(
            course=self.course1,
            title="Scoring Quiz",
            passing_score=70,
            is_published=True
        )
        q1 = Question.objects.create(quiz=quiz, text="Question 1")
        q1_opt1 = Option.objects.create(question=q1, text="Correct 1", is_correct=True)
        q1_opt2 = Option.objects.create(question=q1, text="Wrong 1", is_correct=False)

        q2 = Question.objects.create(quiz=quiz, text="Question 2")
        q2_opt1 = Option.objects.create(question=q2, text="Correct 2", is_correct=True)
        q2_opt2 = Option.objects.create(question=q2, text="Wrong 2", is_correct=False)

        self.client.force_authenticate(user=self.student)

        # 1. Submit 1 correct, 1 wrong -> 50% score -> Fail (< 70%)
        response = self.client.post(f"/api/quizzes/student/{quiz.id}/submit/", {
            "answers": [
                {"question": q1.id, "selected_option": q1_opt1.id},
                {"question": q2.id, "selected_option": q2_opt2.id}
            ]
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["score"], 1)
        self.assertEqual(response.data["total_questions"], 2)
        self.assertEqual(response.data["percentage"], 50)
        self.assertFalse(response.data["is_passed"])

        # 2. Retake quiz: 2 correct -> 100% score -> Pass (>= 70%)
        response2 = self.client.post(f"/api/quizzes/student/{quiz.id}/submit/", {
            "answers": [
                {"question": q1.id, "selected_option": q1_opt1.id},
                {"question": q2.id, "selected_option": q2_opt1.id}
            ]
        }, format="json")
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response2.data["score"], 2)
        self.assertEqual(response2.data["total_questions"], 2)
        self.assertEqual(response2.data["percentage"], 100)
        self.assertTrue(response2.data["is_passed"])

    def test_certificate_gated_by_quiz_completion(self):
        # Set up a course with 1 lesson and 1 published quiz
        quiz = Quiz.objects.create(
            course=self.course1,
            title="Cert Gate Quiz",
            passing_score=70,
            is_published=True
        )
        q1 = Question.objects.create(quiz=quiz, text="Q1")
        opt_correct = Option.objects.create(question=q1, text="Correct", is_correct=True)
        opt_wrong = Option.objects.create(question=q1, text="Wrong", is_correct=False)

        self.client.force_authenticate(user=self.student)

        # Mark lesson as completed
        LessonProgress.objects.create(
            student=self.student,
            lesson=self.lesson1,
            is_completed=True
        )

        # Attempt to claim certificate BEFORE passing quiz -> Should fail
        response = self.client.post("/api/certificates/", {
            "course": self.course1.id
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("pass the course assessment quiz", response.data["error"].lower())

        # Submit failing attempt
        self.client.post(f"/api/quizzes/student/{quiz.id}/submit/", {
            "answers": [{"question": q1.id, "selected_option": opt_wrong.id}]
        }, format="json")
        # Still fails
        response = self.client.post("/api/certificates/", {
            "course": self.course1.id
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Submit passing attempt
        self.client.post(f"/api/quizzes/student/{quiz.id}/submit/", {
            "answers": [{"question": q1.id, "selected_option": opt_correct.id}]
        }, format="json")

        # Claim certificate -> Should succeed now
        response = self.client.post("/api/certificates/", {
            "course": self.course1.id
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["certificate"]["course"], self.course1.id)
