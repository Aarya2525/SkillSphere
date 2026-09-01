from rest_framework import serializers

from .models import LessonProgress


class LessonProgressSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(
        source="student.username",
        read_only=True,
    )

    lesson_title = serializers.CharField(
        source="lesson.title",
        read_only=True,
    )

    course_id = serializers.IntegerField(
        source="lesson.module.course.id",
        read_only=True,
    )

    class Meta:
        model = LessonProgress
        fields = [
            "id",
            "student",
            "student_name",
            "lesson",
            "lesson_title",
            "course_id",
            "is_completed",
            "completed_at",
        ]
        read_only_fields = [
            "student",
            "student_name",
            "lesson_title",
            "course_id",
            "completed_at",
        ]

    def validate(self, attrs):
        student = self.context["request"].user
        lesson = attrs.get("lesson")

        if lesson is not None:
            if LessonProgress.objects.filter(
                student=student,
                lesson=lesson,
            ).exists():
                raise serializers.ValidationError(
                    "Progress for this lesson already exists."
                )

        return attrs