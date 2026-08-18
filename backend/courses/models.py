from django.conf import settings
from django.db import models


class Course(models.Model):
    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="courses",
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class Module(models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="modules",
    )
    title = models.CharField(max_length=200)
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.course.title} - {self.title}"


class Lesson(models.Model):
    module = models.ForeignKey(
        Module,
        on_delete=models.CASCADE,
        related_name="lessons",
    )
    title = models.CharField(max_length=200)
    content = models.TextField()
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.module.title} - {self.title}" 