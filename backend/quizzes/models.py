from django.conf import settings
from django.db import models


class Quiz(models.Model):
    course = models.ForeignKey(
        "courses.Course",
        on_delete=models.CASCADE,
        related_name="quizzes",
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.title


class Question(models.Model):
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name="questions",
    )
    text = models.TextField()
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.text[:50]


class Option(models.Model):
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="options",
    )
    text = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text


class QuizAttempt(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="quiz_attempts",
    )
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name="attempts",
    )
    score = models.PositiveIntegerField(default=0)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.username} - {self.quiz.title}"


class Answer(models.Model):
    attempt = models.ForeignKey(
        QuizAttempt,
        on_delete=models.CASCADE,
        related_name="answers",
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="answers",
    )
    selected_option = models.ForeignKey(
        Option,
        on_delete=models.CASCADE,
        related_name="selected_answers",
    )

    def __str__(self):
        return f"{self.attempt} - {self.question}" 