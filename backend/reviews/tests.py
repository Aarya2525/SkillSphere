"""
Stage 17: Comprehensive testing for Reviews & Ratings.
Covers rating range validation (1-5), enrollment checks, duplicate review prevention,
review update permissions, instructor notification, and course rating aggregation.
"""
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from rest_framework import status
from rest_framework.test import APITestCase

from test_utils.base import FAST_HASHERS_OVERRIDE
from courses.models import Course
from enrollments.models import Enrollment
from notifications.models import Notification
from reviews.models import Review

User = get_user_model()


@FAST_HASHERS_OVERRIDE
class ReviewLifecycleTests(APITestCase):

    def setUp(self):
        self.instructor = User.objects.create_user(
            username="rev_inst",
            email="rev_inst@example.com",
            password="password123",
            role=User.Role.INSTRUCTOR,
        )
        self.student1 = User.objects.create_user(
            username="rev_student1",
            email="rev_student1@example.com",
            password="password123",
            role=User.Role.STUDENT,
        )
        self.student2 = User.objects.create_user(
            username="rev_student2",
            email="rev_student2@example.com",
            password="password123",
            role=User.Role.STUDENT,
        )
        self.admin = User.objects.create_user(
            username="rev_admin",
            email="rev_admin@example.com",
            password="password123",
            role=User.Role.ADMIN,
        )

        self.course = Course.objects.create(
            instructor=self.instructor,
            title="Reviewable Course",
            is_published=True,
        )
        Enrollment.objects.create(student=self.student1, course=self.course)

    # 1. Enrolled student creates review
    def test_enrolled_student_creates_review_success(self):
        self.client.force_authenticate(user=self.student1)
        response = self.client.post("/api/reviews/", {
            "course": self.course.id,
            "rating": 5,
            "comment": "Outstanding course!",
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["rating"], 5)
        self.assertEqual(response.data["comment"], "Outstanding course!")
        self.assertEqual(response.data["course"], self.course.id)

        # Confirm instructor notification generated
        notif = Notification.objects.filter(
            recipient=self.instructor,
            notification_type="REVIEW",
        ).first()
        self.assertIsNotNone(notif)
        self.assertIn("5/5", notif.message)

    # 2. Non-enrolled student cannot review course
    def test_non_enrolled_student_cannot_review(self):
        self.client.force_authenticate(user=self.student2)
        response = self.client.post("/api/reviews/", {
            "course": self.course.id,
            "rating": 4,
            "comment": "Should fail",
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("must be enrolled", str(response.data).lower())

    # 3. Rating range validation: valid values 1 and 5 succeed
    def test_valid_rating_boundaries(self):
        self.client.force_authenticate(user=self.student1)
        response = self.client.post("/api/reviews/", {
            "course": self.course.id,
            "rating": 1,
            "comment": "Lowest valid rating",
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["rating"], 1)

    # 4. Rating range validation: 0 and 6 rejected with 400
    def test_invalid_ratings_rejected(self):
        self.client.force_authenticate(user=self.student1)

        # Rating = 0
        resp0 = self.client.post("/api/reviews/", {
            "course": self.course.id,
            "rating": 0,
            "comment": "Zero rating",
        })
        self.assertEqual(resp0.status_code, status.HTTP_400_BAD_REQUEST)

        # Rating = 6
        resp6 = self.client.post("/api/reviews/", {
            "course": self.course.id,
            "rating": 6,
            "comment": "Too high rating",
        })
        self.assertEqual(resp6.status_code, status.HTTP_400_BAD_REQUEST)

    # 5. Duplicate review prevented
    def test_duplicate_review_rejected(self):
        Review.objects.create(
            student=self.student1,
            course=self.course,
            rating=5,
            comment="First review",
        )
        self.client.force_authenticate(user=self.student1)
        response = self.client.post("/api/reviews/", {
            "course": self.course.id,
            "rating": 4,
            "comment": "Second review",
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("already reviewed", str(response.data).lower())

    # 6. Student can update own review
    def test_student_can_update_own_review(self):
        review = Review.objects.create(
            student=self.student1,
            course=self.course,
            rating=4,
            comment="Initial thought",
        )
        self.client.force_authenticate(user=self.student1)
        response = self.client.patch(f"/api/reviews/{review.id}/", {
            "rating": 5,
            "comment": "Updated thought!",
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["rating"], 5)
        self.assertEqual(response.data["comment"], "Updated thought!")

    # 7. Another student cannot update review -> 403
    def test_student_cannot_update_another_students_review(self):
        review = Review.objects.create(
            student=self.student1,
            course=self.course,
            rating=4,
            comment="Student 1 review",
        )
        self.client.force_authenticate(user=self.student2)
        response = self.client.patch(f"/api/reviews/{review.id}/", {
            "rating": 1,
            "comment": "Malicious edit",
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # 8. Instructor cannot create review -> 403
    def test_instructor_cannot_create_review(self):
        self.client.force_authenticate(user=self.instructor)
        response = self.client.post("/api/reviews/", {
            "course": self.course.id,
            "rating": 5,
            "comment": "Instructor self review",
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # 9. Course rating aggregation endpoint
    def test_course_rating_aggregation(self):
        Enrollment.objects.create(student=self.student2, course=self.course)
        Review.objects.create(student=self.student1, course=self.course, rating=4, comment="Good")
        Review.objects.create(student=self.student2, course=self.course, rating=5, comment="Great")

        self.client.force_authenticate(user=self.student1)
        response = self.client.get(f"/api/reviews/course/{self.course.id}/rating/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["course"], self.course.id)
        self.assertEqual(response.data["total_reviews"], 2)
        self.assertEqual(response.data["average_rating"], 4.5)

    # 10. Database unique constraint on (student, course)
    def test_database_unique_constraint_on_review(self):
        Review.objects.create(student=self.student1, course=self.course, rating=5, comment="R1")
        with self.assertRaises(IntegrityError):
            Review.objects.create(student=self.student1, course=self.course, rating=4, comment="R2")

    # 11. Regression: Student can delete their own review
    def test_student_can_delete_own_review(self):
        review = Review.objects.create(
            student=self.student1,
            course=self.course,
            rating=5,
            comment="Delete me",
        )
        self.client.force_authenticate(user=self.student1)
        response = self.client.delete(f"/api/reviews/{review.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Review.objects.filter(id=review.id).exists())

    # 12. Regression: Student cannot delete another student's review (ownership protection)
    def test_student_cannot_delete_another_students_review(self):
        review = Review.objects.create(
            student=self.student1,
            course=self.course,
            rating=5,
            comment="Protected review",
        )
        self.client.force_authenticate(user=self.student2)
        response = self.client.delete(f"/api/reviews/{review.id}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Review.objects.filter(id=review.id).exists())

    # 13. Regression: Admin can delete/moderate any review
    def test_admin_can_delete_any_review(self):
        review = Review.objects.create(
            student=self.student1,
            course=self.course,
            rating=1,
            comment="Spam review",
        )
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(f"/api/reviews/{review.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Review.objects.filter(id=review.id).exists())
