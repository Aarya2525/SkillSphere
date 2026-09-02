from django.urls import path

from .views import (
    ReviewListCreateView,
    ReviewDetailView,
    CourseRatingView,
)

urlpatterns = [
    path(
        "",
        ReviewListCreateView.as_view(),
        name="review-list-create",
    ),
    path(
        "<int:pk>/",
        ReviewDetailView.as_view(),
        name="review-detail",
    ),
    path(
        "course/<int:course_id>/rating/",
        CourseRatingView.as_view(),
        name="course-rating",
    ),
] 