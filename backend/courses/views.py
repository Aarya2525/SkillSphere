from rest_framework import generics
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated

from .models import Course, Module, Lesson
from .serializers import (
    CourseSerializer,
    ModuleSerializer,
    LessonSerializer,
)


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


class CourseDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if user.role == "ADMIN":
            return Course.objects.all()

        if user.role == "INSTRUCTOR":
            return Course.objects.filter(instructor=user)

        return Course.objects.filter(is_published=True)

    def perform_update(self, serializer):
        if self.request.user.role not in ["INSTRUCTOR", "ADMIN"]:
            raise PermissionDenied(
                "Only instructors and admins can update courses."
            )

        serializer.save()

    def perform_destroy(self, instance):
        if self.request.user.role not in ["INSTRUCTOR", "ADMIN"]:
            raise PermissionDenied(
                "Only instructors and admins can delete courses."
            )

        instance.delete()


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


class ModuleDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ModuleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if user.role == "ADMIN":
            return Module.objects.all()

        if user.role == "INSTRUCTOR":
            return Module.objects.filter(course__instructor=user)

        return Module.objects.filter(course__is_published=True)

    def perform_update(self, serializer):
        if self.request.user.role not in ["INSTRUCTOR", "ADMIN"]:
            raise PermissionDenied(
                "Only instructors and admins can update modules."
            )

        serializer.save()

    def perform_destroy(self, instance):
        if self.request.user.role not in ["INSTRUCTOR", "ADMIN"]:
            raise PermissionDenied(
                "Only instructors and admins can delete modules."
            )

        instance.delete()


class LessonListCreateView(generics.ListCreateAPIView):
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Lesson.objects.all()

    def perform_create(self, serializer):
        module = serializer.validated_data["module"]
        course = module.course

        if (
            self.request.user.role != "ADMIN"
            and course.instructor != self.request.user
        ):
            raise PermissionDenied(
                "You can only add lessons to your own courses."
            )

        serializer.save()


class LessonDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if user.role == "ADMIN":
            return Lesson.objects.all()

        if user.role == "INSTRUCTOR":
            return Lesson.objects.filter(
                module__course__instructor=user
            )

        return Lesson.objects.filter(
            module__course__is_published=True
        )

    def perform_update(self, serializer):
        if self.request.user.role not in ["INSTRUCTOR", "ADMIN"]:
            raise PermissionDenied(
                "Only instructors and admins can update lessons."
            )

        serializer.save()

    def perform_destroy(self, instance):
        if self.request.user.role not in ["INSTRUCTOR", "ADMIN"]:
            raise PermissionDenied(
                "Only instructors and admins can delete lessons."
            )

        instance.delete() 