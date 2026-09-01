from django.urls import path

from .views import (
    LessonProgressListCreateView,
    LessonProgressDetailView,
)


urlpatterns = [
    path(
        "progress/",
        LessonProgressListCreateView.as_view(),
        name="lesson-progress-list-create",
    ),

    path(
        "progress/<int:pk>/",
        LessonProgressDetailView.as_view(),
        name="lesson-progress-detail",
    ),
] 