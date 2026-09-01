from rest_framework import generics
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated

from .models import Enrollment
from .serializers import EnrollmentSerializer


class EnrollmentListCreateView(generics.ListCreateAPIView):
    serializer_class = EnrollmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if user.role == "ADMIN":
            return Enrollment.objects.all()

        return Enrollment.objects.filter(student=user)

    def perform_create(self, serializer):
        user = self.request.user

        if user.role != "STUDENT":
            raise PermissionDenied(
                "Only students can enroll in courses."
            )

        course = serializer.validated_data["course"]

        if not course.is_published:
            raise PermissionDenied(
                "You can only enroll in published courses."
            )

        if Enrollment.objects.filter(
            student=user,
            course=course,
        ).exists():
            raise ValidationError(
                "You are already enrolled in this course."
            )

        serializer.save(student=user) 