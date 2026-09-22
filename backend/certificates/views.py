from django.db import IntegrityError
from django.shortcuts import get_object_or_404

from rest_framework import generics
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from courses.models import Course, Lesson
from enrollments.models import Enrollment
from learning.models import LessonProgress
from notifications.models import Notification

from .models import Certificate
from .serializers import CertificateSerializer


# ============================================================
# STUDENT CERTIFICATE GENERATION
# ============================================================

class CertificateCreateView(generics.CreateAPIView):
    serializer_class = CertificateSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        student = request.user

        # --------------------------------------------------------
        # Only students can generate certificates
        # --------------------------------------------------------

        if student.role != "STUDENT":
            raise PermissionDenied(
                "Only students can generate certificates."
            )

        course_id = request.data.get("course")

        if not course_id:
            return Response(
                {
                    "error": "Course ID is required."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # --------------------------------------------------------
        # Get course
        # --------------------------------------------------------

        course = get_object_or_404(
            Course,
            id=course_id,
        )

        # --------------------------------------------------------
        # Check enrollment
        # --------------------------------------------------------

        if not Enrollment.objects.filter(
            student=student,
            course=course,
        ).exists():
            raise PermissionDenied(
                "You must be enrolled in this course."
            )

        # --------------------------------------------------------
        # Get all course lessons
        # --------------------------------------------------------

        total_lessons = Lesson.objects.filter(
            module__course=course
        ).count()

        if total_lessons == 0:
            return Response(
                {
                    "error": (
                        "Certificate cannot be issued because "
                        "this course has no lessons."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # --------------------------------------------------------
        # Count completed lessons
        # --------------------------------------------------------

        completed_lessons = LessonProgress.objects.filter(
            student=student,
            lesson__module__course=course,
            is_completed=True,
        ).count()

        # --------------------------------------------------------
        # Calculate completion percentage
        # --------------------------------------------------------

        completion_percentage = round(
            (completed_lessons / total_lessons) * 100
        )

        # --------------------------------------------------------
        # Require 100% completion
        # --------------------------------------------------------

        if completion_percentage < 100:
            return Response(
                {
                    "error": "Course is not completed yet.",
                    "course": course.id,
                    "course_title": course.title,
                    "completed_lessons": completed_lessons,
                    "total_lessons": total_lessons,
                    "completion_percentage": completion_percentage,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # --------------------------------------------------------
        # Require quiz passed if course has published quizzes
        # --------------------------------------------------------

        published_quizzes = course.quizzes.filter(is_published=True)

        if published_quizzes.exists():
            from quizzes.models import QuizAttempt

            has_passed_quiz = QuizAttempt.objects.filter(
                student=student,
                quiz__in=published_quizzes,
                is_passed=True,
            ).exists()

            if not has_passed_quiz:
                return Response(
                    {
                        "error": (
                            "You must pass the course assessment quiz "
                            "before claiming your certificate."
                        ),
                        "course": course.id,
                        "course_title": course.title,
                        "quiz_required": True,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # --------------------------------------------------------
        # Prevent duplicate certificate
        # --------------------------------------------------------

        existing_certificate = Certificate.objects.filter(
            student=student,
            course=course,
        ).first()

        if existing_certificate:
            return Response(
                {
                    "message": "Certificate already exists.",
                    "certificate": CertificateSerializer(
                        existing_certificate
                    ).data,
                },
                status=status.HTTP_200_OK,
            )

        # --------------------------------------------------------
        # Create certificate
        # --------------------------------------------------------

        try:
            certificate = Certificate.objects.create(
                student=student,
                course=course,
                completion_percentage=completion_percentage,
            )

        except IntegrityError:
            certificate = Certificate.objects.get(
                student=student,
                course=course,
            )

        # --------------------------------------------------------
        # Create certificate notification
        # --------------------------------------------------------

        Notification.objects.create(
            recipient=student,
            notification_type="CERTIFICATE",
            title="Certificate Earned",
            message=(
                f"Congratulations! You have completed "
                f"{course.title} and earned your certificate."
            ),
        )

        # --------------------------------------------------------
        # Return certificate
        # --------------------------------------------------------

        return Response(
            {
                "message": "Certificate issued successfully.",
                "certificate": CertificateSerializer(
                    certificate
                ).data,
            },
            status=status.HTTP_201_CREATED,
        )


# ============================================================
# STUDENT CERTIFICATE LIST
# ============================================================

class StudentCertificateListView(generics.ListAPIView):
    serializer_class = CertificateSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        student = self.request.user

        if student.role != "STUDENT":
            raise PermissionDenied(
                "Only students can view their certificates."
            )

        return Certificate.objects.filter(
            student=student
        ).select_related(
            "student",
            "course",
        )


# ============================================================
# STUDENT CERTIFICATE DETAIL
# ============================================================

class StudentCertificateDetailView(generics.RetrieveAPIView):
    serializer_class = CertificateSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        student = self.request.user

        if student.role != "STUDENT":
            raise PermissionDenied(
                "Only students can view their certificates."
            )

        return Certificate.objects.filter(
            student=student
        ).select_related(
            "student",
            "course",
        )


# ============================================================
# PUBLIC CERTIFICATE VERIFICATION
# ============================================================

class CertificateVerifyView(generics.RetrieveAPIView):
    serializer_class = CertificateSerializer
    permission_classes = []

    lookup_field = "certificate_id"
    lookup_url_kwarg = "certificate_id"

    def get_queryset(self):
        return Certificate.objects.select_related(
            "student",
            "course",
        ) 