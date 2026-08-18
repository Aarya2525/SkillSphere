from rest_framework import generics
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated

from .models import Course, Module
from .serializers import CourseSerializer, ModuleSerializer


class CourseListCreateView(generics.ListCreateAPIView):
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if user.role == "ADMIN":
            return Course.objects.all()

        if user.role == "INSTRUCTOR":
            return Course.objects.filter(instructor=user)

        return Course.objects.filter(is_published=True)

    def perform_create(self, serializer):
        if self.request.user.role not in ["INSTRUCTOR", "ADMIN"]:
            raise PermissionDenied(
                "Only instructors and admins can create courses."
            )

        serializer.save(instructor=self.request.user)


class ModuleListCreateView(generics.ListCreateAPIView):
    serializer_class = ModuleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Module.objects.all()

    def perform_create(self, serializer):
        course = serializer.validated_data["course"]

        if (
            self.request.user.role != "ADMIN"
            and course.instructor != self.request.user
        ):
            raise PermissionDenied(
                "You can only add modules to your own courses."
            )

        serializer.save() 