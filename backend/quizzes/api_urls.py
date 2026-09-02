from django.urls import path

from .views import (
    QuizListCreateView,
    QuizDetailView,
    StudentQuizDetailView,
    QuizSubmitView,
    StudentQuizAttemptListView,
    StudentQuizAttemptDetailView,
    InstructorQuizAttemptListView,
    QuestionListCreateView,
    QuestionDetailView,
    OptionListCreateView,
    OptionDetailView,
)


urlpatterns = [
    # ============================================================
    # QUIZZES
    # ============================================================

    path(
        "",
        QuizListCreateView.as_view(),
        name="quiz-list-create",
    ),

    path(
        "<int:pk>/",
        QuizDetailView.as_view(),
        name="quiz-detail",
    ),

    # ============================================================
    # STUDENT QUIZ
    # ============================================================

    path(
        "student/<int:pk>/",
        StudentQuizDetailView.as_view(),
        name="student-quiz-detail",
    ),

    path(
        "student/<int:pk>/submit/",
        QuizSubmitView.as_view(),
        name="quiz-submit",
    ),

    # ============================================================
    # STUDENT ATTEMPTS / RESULTS
    # ============================================================

    path(
        "attempts/",
        StudentQuizAttemptListView.as_view(),
        name="student-quiz-attempt-list",
    ),

    path(
        "attempts/<int:pk>/",
        StudentQuizAttemptDetailView.as_view(),
        name="student-quiz-attempt-detail",
    ),

    # ============================================================
    # INSTRUCTOR / ADMIN ATTEMPTS
    # ============================================================

    path(
        "instructor/attempts/",
        InstructorQuizAttemptListView.as_view(),
        name="instructor-quiz-attempt-list",
    ),

    # ============================================================
    # QUESTIONS
    # ============================================================

    path(
        "questions/",
        QuestionListCreateView.as_view(),
        name="question-list-create",
    ),

    path(
        "questions/<int:pk>/",
        QuestionDetailView.as_view(),
        name="question-detail",
    ),

    # ============================================================
    # OPTIONS
    # ============================================================

    path(
        "options/",
        OptionListCreateView.as_view(),
        name="option-list-create",
    ),

    path(
        "options/<int:pk>/",
        OptionDetailView.as_view(),
        name="option-detail",
    ),
] 