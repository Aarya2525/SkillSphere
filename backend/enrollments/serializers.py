from rest_framework import serializers

from .models import Enrollment


class EnrollmentSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(
        source="student.username",
        read_only=True,
    )

    course_title = serializers.CharField(
        source="course.title",
        read_only=True,
    )

    class Meta:
        model = Enrollment
        fields = [
            "id",
            "student",
            "student_name",
            "course",
            "course_title",
            "enrolled_at",
        ]
        read_only_fields = [
            "student",
            "student_name",
            "course_title",
            "enrolled_at",
        ] 