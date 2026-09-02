from django.db.models import Avg
from django.shortcuts import get_object_or_404

from rest_framework import generics
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from courses.models import Course
from enrollments.models import Enrollment
from notifications.models import Notification

from .models import Review
from .serializers import ReviewSerializer


class ReviewListCreateView(generics.ListCreateAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        course_id = self.request.query_params.get("course")

        queryset = Review.objects.select_related(
            "student",
            "course",
        )

        if course_id:
            queryset = queryset.filter(course_id=course_id)

        return queryset

    def perform_create(self, serializer):
        student = self.request.user

        if student.role != "STUDENT":
            raise PermissionDenied(
                "Only students can create reviews."
            )

        course_id = serializer.validated_data["course"].id
        course = get_object_or_404(Course, id=course_id)

        if not course.is_published:
            raise PermissionDenied(
                "You can only review published courses."
            )

        if not Enrollment.objects.filter(
            student=student,
            course=course,
        ).exists():
            raise PermissionDenied(
                "You must be enrolled in this course to review it."
            )

        if Review.objects.filter(
            student=student,
            course=course,
        ).exists():
            raise PermissionDenied(
                "You have already reviewed this course."
            )

        # --------------------------------------------------------
        # Create review
        # --------------------------------------------------------

        review = serializer.save(student=student)

        # --------------------------------------------------------
        # Notify course instructor
        # --------------------------------------------------------

        Notification.objects.create(
            recipient=course.instructor,
            notification_type="REVIEW",
            title="New Course Review",
            message=(
                f"{student.username} reviewed your course "
                f"{course.title} with a rating of "
                f"{review.rating}/5."
            ),
        )


class ReviewDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Review.objects.select_related(
            "student",
            "course",
        )

    def perform_update(self, serializer):
        student = self.request.user
        review = self.get_object()

        if student.role == "ADMIN":
            serializer.save()
            return

        if review.student != student:
            raise PermissionDenied(
                "You can only update your own review."
            )

        if student.role != "STUDENT":
            raise PermissionDenied(
                "Only students can update reviews."
            )

        serializer.save()

    def perform_destroy(self, instance):
        student = self.request.user

        if student.role == "ADMIN":
            instance.delete()
            return

        if instance.student != student:
            raise PermissionDenied(
                "You can only delete your own review."
            )

        instance.delete()


class CourseRatingView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]

    def retrieve(self, request, *args, **kwargs):
        course = get_object_or_404(
            Course,
            id=kwargs["course_id"],
        )

        reviews = Review.objects.filter(course=course)

        average_rating = reviews.aggregate(
            average=Avg("rating")
        )["average"]

        return Response({
            "course": course.id,
            "course_title": course.title,
            "average_rating": round(average_rating, 2)
            if average_rating is not None
            else 0,
            "total_reviews": reviews.count(),
        }) 