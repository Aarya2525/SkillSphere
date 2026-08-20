from django.urls import path

from .views import (
    CourseListCreateView,
    CourseDetailView,
    ModuleListCreateView,
    ModuleDetailView,
    LessonListCreateView,
    LessonDetailView,
)


urlpatterns = [
    # Courses
    path(
        "",
        CourseListCreateView.as_view(),
        name="course-list-create",
    ),
    path(
        "<int:pk>/",
        CourseDetailView.as_view(),
        name="course-detail",
    ),

    # Modules
    path(
        "modules/",
        ModuleListCreateView.as_view(),
        name="module-list-create",
    ),
    path(
        "modules/<int:pk>/",
        ModuleDetailView.as_view(),
        name="module-detail",
    ),

    # Lessons
    path(
        "lessons/",
        LessonListCreateView.as_view(),
        name="lesson-list-create",
    ),
    path(
        "lessons/<int:pk>/",
        LessonDetailView.as_view(),
        name="lesson-detail",
    ),
] 