from django.urls import path

from .views import (
    LessonProgressListCreateView,
    LessonProgressDetailView,
)


urlpatterns = [
    # List progress records / create progress
    path(
        "progress/",
        LessonProgressListCreateView.as_view(),
        name="lesson-progress-list-create",
    ),

    # Retrieve / update / delete specific progress
    path(
        "progress/<int:pk>/",
        LessonProgressDetailView.as_view(),
        name="lesson-progress-detail",
    ),
] 