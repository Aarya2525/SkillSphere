from django.db import transaction

from rest_framework import generics, serializers
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from notifications.models import Notification

from .models import (
    Quiz,
    Question,
    Option,
    QuizAttempt,
    Answer,
)

from .serializers import (
    QuizSerializer,
    QuestionSerializer,
    OptionSerializer,
    StudentQuizSerializer,
    QuizSubmissionSerializer,
    QuizAttemptSerializer,
    InstructorQuizAttemptSerializer,
)


# ============================================================
# QUIZ MANAGEMENT
# ============================================================

class QuizListCreateView(generics.ListCreateAPIView):
    serializer_class = QuizSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Quiz.objects.all()

    def perform_create(self, serializer):
        user = self.request.user

        if user.role not in ["INSTRUCTOR", "ADMIN"]:
            raise PermissionDenied(
                "Only instructors and admins can create quizzes."
            )

        serializer.save()


class QuizDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = QuizSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Quiz.objects.all()

    def perform_update(self, serializer):
        user = self.request.user

        if user.role not in ["INSTRUCTOR", "ADMIN"]:
            raise PermissionDenied(
                "Only instructors and admins can update quizzes."
            )

        serializer.save()

    def perform_destroy(self, instance):
        user = self.request.user

        if user.role not in ["INSTRUCTOR", "ADMIN"]:
            raise PermissionDenied(
                "Only instructors and admins can delete quizzes."
            )

        instance.delete()


# ============================================================
# QUESTION MANAGEMENT
# ============================================================

class QuestionListCreateView(generics.ListCreateAPIView):
    serializer_class = QuestionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Question.objects.all()

    def perform_create(self, serializer):
        user = self.request.user

        if user.role not in ["INSTRUCTOR", "ADMIN"]:
            raise PermissionDenied(
                "Only instructors and admins can create questions."
            )

        serializer.save()


class QuestionDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = QuestionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Question.objects.all()

    def perform_update(self, serializer):
        user = self.request.user

        if user.role not in ["INSTRUCTOR", "ADMIN"]:
            raise PermissionDenied(
                "Only instructors and admins can update questions."
            )

        serializer.save()

    def perform_destroy(self, instance):
        user = self.request.user

        if user.role not in ["INSTRUCTOR", "ADMIN"]:
            raise PermissionDenied(
                "Only instructors and admins can delete questions."
            )

        instance.delete()


# ============================================================
# OPTION MANAGEMENT
# ============================================================

class OptionListCreateView(generics.ListCreateAPIView):
    serializer_class = OptionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Option.objects.all()

    def perform_create(self, serializer):
        user = self.request.user

        if user.role not in ["INSTRUCTOR", "ADMIN"]:
            raise PermissionDenied(
                "Only instructors and admins can create options."
            )

        serializer.save()


class OptionDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = OptionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Option.objects.all()

    def perform_update(self, serializer):
        user = self.request.user

        if user.role not in ["INSTRUCTOR", "ADMIN"]:
            raise PermissionDenied(
                "Only instructors and admins can update options."
            )

        serializer.save()

    def perform_destroy(self, instance):
        user = self.request.user

        if user.role not in ["INSTRUCTOR", "ADMIN"]:
            raise PermissionDenied(
                "Only instructors and admins can delete options."
            )

        instance.delete()


# ============================================================
# STUDENT QUIZ
# ============================================================

class StudentQuizDetailView(generics.RetrieveAPIView):
    serializer_class = StudentQuizSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Quiz.objects.all()


# ============================================================
# QUIZ SUBMISSION
# ============================================================

class QuizSubmitView(generics.CreateAPIView):
    serializer_class = QuizSubmissionSerializer
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        student = request.user

        if student.role != "STUDENT":
            raise PermissionDenied(
                "Only students can submit quizzes."
            )

        quiz = serializer.validated_data["quiz"]
        answers = serializer.validated_data["answers"]

        # --------------------------------------------------------
        # Require all questions to be answered
        # --------------------------------------------------------

        total_questions = quiz.questions.count()

        if len(answers) != total_questions:
            raise serializers.ValidationError(
                {
                    "answers": (
                        f"All questions must be answered. "
                        f"Expected {total_questions}, "
                        f"received {len(answers)}."
                    )
                }
            )

        # --------------------------------------------------------
        # Calculate score on server
        # --------------------------------------------------------

        score = 0

        for answer in answers:
            selected_option = answer["selected_option"]

            if selected_option.is_correct:
                score += 1

        # --------------------------------------------------------
        # Create quiz attempt
        # --------------------------------------------------------

        attempt = QuizAttempt.objects.create(
            student=student,
            quiz=quiz,
            score=score,
        )

        # --------------------------------------------------------
        # Save submitted answers
        # --------------------------------------------------------

        Answer.objects.bulk_create(
            [
                Answer(
                    attempt=attempt,
                    question=answer["question"],
                    selected_option=answer["selected_option"],
                )
                for answer in answers
            ]
        )

        # --------------------------------------------------------
        # Create notification
        # --------------------------------------------------------

        Notification.objects.create(
            recipient=student,
            notification_type="QUIZ",
            title="Quiz Submitted Successfully",
            message=(
                f"You scored {score}/{total_questions} "
                f"in {quiz.title}."
            ),
        )

        # --------------------------------------------------------
        # Response
        # --------------------------------------------------------

        return Response(
            {
                "message": "Quiz submitted successfully.",
                "attempt_id": attempt.id,
                "quiz": quiz.id,
                "score": score,
                "total_questions": total_questions,
            },
            status=201,
        )


# ============================================================
# STUDENT QUIZ RESULT
# ============================================================

class StudentQuizAttemptDetailView(generics.RetrieveAPIView):
    serializer_class = QuizAttemptSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if user.role != "STUDENT":
            raise PermissionDenied(
                "Only students can view student quiz attempts."
            )

        return QuizAttempt.objects.filter(
            student=user
        ).prefetch_related(
            "answers__question",
            "answers__selected_option",
        )


# ============================================================
# STUDENT QUIZ ATTEMPT HISTORY
# ============================================================

class StudentQuizAttemptListView(generics.ListAPIView):
    serializer_class = QuizAttemptSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if user.role != "STUDENT":
            raise PermissionDenied(
                "Only students can view quiz attempt history."
            )

        return QuizAttempt.objects.filter(
            student=user
        ).prefetch_related(
            "answers__question",
            "answers__selected_option",
        ).order_by(
            "-submitted_at"
        )


# ============================================================
# INSTRUCTOR / ADMIN QUIZ ATTEMPTS
# ============================================================

class InstructorQuizAttemptListView(generics.ListAPIView):
    serializer_class = InstructorQuizAttemptSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if user.role not in ["INSTRUCTOR", "ADMIN"]:
            raise PermissionDenied(
                "Only instructors and admins can view quiz attempts."
            )

        return QuizAttempt.objects.select_related(
            "student",
            "quiz",
        ).order_by(
            "-submitted_at"
        ) 