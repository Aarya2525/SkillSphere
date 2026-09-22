from django.contrib import admin

from .models import Course, Module, Lesson


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "instructor",
        "is_published",
        "created_at",
    )

    list_filter = (
        "is_published",
        "created_at",
    )

    search_fields = (
        "title",
        "description",
    )


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "course",
        "order",
    )

    list_filter = (
        "course",
    )

    search_fields = (
        "title",
    )


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "module",
        "order",
    )

    list_filter = (
        "module",
    )

    search_fields = (
        "title",
    ) 