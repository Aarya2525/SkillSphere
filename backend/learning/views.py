from django.utils import timezone

from rest_framework import generics
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated

from .models import LessonProgress
from .serializers import LessonProgressSerializer


class LessonProgressListCreateView(generics.ListCreateAPIView):
    serializer_class = LessonProgressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if user.role == "ADMIN":
            return LessonProgress.objects.all()

        return LessonProgress.objects.filter(student=user)

    def perform_create(self, serializer):
        user = self.request.user

        if user.role != "STUDENT":
            raise PermissionDenied(
                "Only students can create lesson progress."
            )

        lesson = serializer.validated_data["lesson"]
        course = lesson.module.course

        if not course.is_published:
            raise PermissionDenied(
                "You can only access lessons from published courses."
            )

        from enrollments.models import Enrollment

        if not Enrollment.objects.filter(
            student=user,
            course=course,
        ).exists():
            raise PermissionDenied(
                "You must be enrolled in this course."
            )

        is_completed = serializer.validated_data.get(
            "is_completed",
            False,
        )

        if is_completed:
            serializer.save(
                student=user,
                completed_at=timezone.now(),
            )
        else:
            serializer.save(student=user)


class LessonProgressDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = LessonProgressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if user.role == "ADMIN":
            return LessonProgress.objects.all()

        return LessonProgress.objects.filter(student=user)

    def perform_update(self, serializer):
        user = self.request.user

        if user.role != "STUDENT":
            raise PermissionDenied(
                "Only students can update lesson progress."
            )

        is_completed = serializer.validated_data.get(
            "is_completed",
            serializer.instance.is_completed,
        )

        if is_completed:
            serializer.save(
                completed_at=timezone.now(),
            )
        else:
            serializer.save(
                completed_at=None,
            )

    def perform_destroy(self, instance):
        user = self.request.user

        if user.role not in ["STUDENT", "ADMIN"]:
            raise PermissionDenied(
                "Only students and admins can delete lesson progress."
            )

        instance.delete() 