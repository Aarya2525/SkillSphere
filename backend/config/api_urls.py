from django.urls import include, path

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from accounts.views import (
    CurrentUserView,
    RegisterView,
    StudentTestView,
    InstructorTestView,
    AdminTestView,
)


urlpatterns = [
    # ============================================================
    # AUTHENTICATION
    # ============================================================

    path(
        "auth/register/",
        RegisterView.as_view(),
        name="register",
    ),

    path(
        "auth/token/",
        TokenObtainPairView.as_view(),
        name="token_obtain_pair",
    ),

    path(
        "auth/token/refresh/",
        TokenRefreshView.as_view(),
        name="token_refresh",
    ),

    path(
        "auth/me/",
        CurrentUserView.as_view(),
        name="current_user",
    ),

    # ============================================================
    # ROLE TESTING
    # ============================================================

    path(
        "student-test/",
        StudentTestView.as_view(),
        name="student_test",
    ),

    path(
        "instructor-test/",
        InstructorTestView.as_view(),
        name="instructor_test",
    ),

    path(
        "admin-test/",
        AdminTestView.as_view(),
        name="admin_test",
    ),

    # ============================================================
    # COURSES
    # ============================================================

    path(
        "courses/",
        include("courses.urls"),
    ),

    # ============================================================
    # ENROLLMENTS
    # ============================================================

    path(
        "enrollments/",
        include("enrollments.urls"),
    ),

    # ============================================================
    # LEARNING / PROGRESS
    # ============================================================

    path(
        "learning/",
        include("learning.urls"),
    ),

    # ============================================================
    # QUIZZES
    # ============================================================

    path(
        "quizzes/",
        include("quizzes.api_urls"),
    ),

    # ============================================================
    # CERTIFICATES
    # ============================================================

    path(
        "certificates/",
        include("certificates.api_urls"),
    ),

    # ============================================================
    # REVIEWS & RATINGS
    # ============================================================

    path(
        "reviews/",
        include("reviews.urls"),
    ),
] 