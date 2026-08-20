from rest_framework import serializers

from .models import Course, Module, Lesson


class CourseSerializer(serializers.ModelSerializer):
    instructor_name = serializers.CharField(
        source="instructor.username",
        read_only=True,
    )

    class Meta:
        model = Course
        fields = [
            "id",
            "instructor",
            "instructor_name",
            "title",
            "description",
            "is_published",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "instructor",
            "created_at",
            "updated_at",
        ]


class ModuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Module
        fields = [
            "id",
            "course",
            "title",
            "order",
        ]


class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = [
            "id",
            "module",
            "title",
            "content",
            "order",
        ] 