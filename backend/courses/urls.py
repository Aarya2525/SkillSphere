from django.urls import path

from .views import (
    CourseListCreateView,
    ModuleListCreateView,
    LessonListCreateView,
)


urlpatterns = [
    path(
        "",
        CourseListCreateView.as_view(),
        name="course-list-create",
    ),
    path(
        "modules/",
        ModuleListCreateView.as_view(),
        name="module-list-create",
    ),
    path(
        "lessons/",
        LessonListCreateView.as_view(),
        name="lesson-list-create",
    ),
] 