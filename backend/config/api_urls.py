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
    # Authentication
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
    # Role Testing
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
    # Courses
    # ============================================================

    path(
        "courses/",
        include("courses.urls"),
    ),

    # ============================================================
    # Enrollments
    # ============================================================

    path(
        "enrollments/",
        include("enrollments.urls"),
    ),

    # ============================================================
    # Learning / Progress
    # ============================================================

    path(
        "learning/",
        include("learning.urls"),
    ),
] 