import uuid

from django.conf import settings
from django.db import models


class Certificate(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="certificates",
    )

    course = models.ForeignKey(
        "courses.Course",
        on_delete=models.CASCADE,
        related_name="certificates",
    )

    certificate_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )

    issued_at = models.DateTimeField(
        auto_now_add=True,
    )

    completion_percentage = models.PositiveIntegerField(
        default=100,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["student", "course"],
                name="unique_student_course_certificate",
            )
        ]
        ordering = ["-issued_at"]

    def __str__(self):
        return (
            f"{self.student.username} - "
            f"{self.course.title}"
        ) 