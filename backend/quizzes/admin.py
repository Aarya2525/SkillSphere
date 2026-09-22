from django.contrib import admin

from .models import (
    Quiz,
    Question,
    Option,
    QuizAttempt,
    Answer,
)


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "course",
    )
    list_filter = (
        "course",
    )
    search_fields = (
        "title",
        "description",
    )


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "quiz",
        "text",
        "order",
    )
    list_filter = (
        "quiz",
    )
    search_fields = (
        "text",
    )


@admin.register(Option)
class OptionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "question",
        "text",
        "is_correct",
    )
    list_filter = (
        "is_correct",
        "question",
    )
    search_fields = (
        "text",
    )


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "student",
        "quiz",
        "score",
        "submitted_at",
    )
    list_filter = (
        "quiz",
        "submitted_at",
    )


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "attempt",
        "question",
        "selected_option",
    )
    list_filter = (
        "attempt",
        "question",
        "selected_option",
    ) 