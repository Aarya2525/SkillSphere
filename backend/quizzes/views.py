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


def validate_quiz_for_publishing(quiz):
    """
    Validate quiz structure before publishing:
    - Must have at least one question.
    - Each question must have valid options (at least 2).
    - Each question must have exactly one correct option.
    """
    questions = quiz.questions.all()
    if not questions.exists():
        raise serializers.ValidationError(
            "A quiz must have at least one question before it can be published."
        )

    for question in questions:
        options = question.options.all()
        if options.count() < 2:
            raise serializers.ValidationError(
                f"Question '{question.text[:30]}' must have at least 2 options before publishing."
            )
        correct_count = options.filter(is_correct=True).count()
        if correct_count != 1:
            raise serializers.ValidationError(
                f"Question '{question.text[:30]}' must have exactly one correct option (currently has {correct_count})."
            )


# ============================================================
# QUIZ MANAGEMENT
# ============================================================

class QuizListCreateView(generics.ListCreateAPIView):
    serializer_class = QuizSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        course_id = self.request.query_params.get("course")

        if user.role == "ADMIN":
            queryset = Quiz.objects.all()
        elif user.role == "INSTRUCTOR":
            queryset = Quiz.objects.filter(course__instructor=user)
        else:
            # Student: only published quizzes of published courses the student is enrolled in
            queryset = Quiz.objects.filter(
                is_published=True,
                course__is_published=True,
                course__enrollments__student=user,
            )

        if course_id:
            queryset = queryset.filter(course_id=course_id)

        return queryset.distinct()

    def perform_create(self, serializer):
        user = self.request.user

        if user.role not in ["INSTRUCTOR", "ADMIN"]:
            raise PermissionDenied(
                "Only instructors and admins can create quizzes."
            )

        course = serializer.validated_data["course"]

        if user.role != "ADMIN" and course.instructor != user:
            raise PermissionDenied(
                "You can only create quizzes for your own courses."
            )

        is_published = serializer.validated_data.get("is_published", False)
        if is_published:
            raise serializers.ValidationError(
                "A new quiz cannot be published before adding questions and options."
            )

        serializer.save()


class QuizDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = QuizSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if user.role == "ADMIN":
            return Quiz.objects.all()

        if user.role == "INSTRUCTOR":
            return Quiz.objects.filter(course__instructor=user)

        return Quiz.objects.filter(
            is_published=True,
            course__is_published=True,
        )

    def perform_update(self, serializer):
        user = self.request.user
        quiz = serializer.instance

        if user.role not in ["INSTRUCTOR", "ADMIN"]:
            raise PermissionDenied(
                "Only instructors and admins can update quizzes."
            )

        if user.role != "ADMIN" and quiz.course.instructor != user:
            raise PermissionDenied(
                "You can only update quizzes for your own courses."
            )

        target_published = serializer.validated_data.get(
            "is_published",
            quiz.is_published,
        )

        if target_published and not quiz.is_published:
            validate_quiz_for_publishing(quiz)

        serializer.save()

    def perform_destroy(self, instance):
        user = self.request.user

        if user.role not in ["INSTRUCTOR", "ADMIN"]:
            raise PermissionDenied(
                "Only instructors and admins can delete quizzes."
            )

        if user.role != "ADMIN" and instance.course.instructor != user:
            raise PermissionDenied(
                "You can only delete quizzes for your own courses."
            )

        instance.delete()


# ============================================================
# QUESTION MANAGEMENT
# ============================================================

class QuestionListCreateView(generics.ListCreateAPIView):
    serializer_class = QuestionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        quiz_id = self.request.query_params.get("quiz")

        if user.role == "ADMIN":
            qs = Question.objects.all()
        elif user.role == "INSTRUCTOR":
            qs = Question.objects.filter(quiz__course__instructor=user)
        else:
            qs = Question.objects.filter(
                quiz__is_published=True,
                quiz__course__is_published=True,
            )

        if quiz_id:
            qs = qs.filter(quiz_id=quiz_id)

        return qs

    def perform_create(self, serializer):
        user = self.request.user

        if user.role not in ["INSTRUCTOR", "ADMIN"]:
            raise PermissionDenied(
                "Only instructors and admins can create questions."
            )

        quiz = serializer.validated_data["quiz"]

        if user.role != "ADMIN" and quiz.course.instructor != user:
            raise PermissionDenied(
                "You can only add questions to your own quizzes."
            )

        serializer.save()


class QuestionDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = QuestionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if user.role == "ADMIN":
            return Question.objects.all()

        if user.role == "INSTRUCTOR":
            return Question.objects.filter(quiz__course__instructor=user)

        return Question.objects.filter(
            quiz__is_published=True,
            quiz__course__is_published=True,
        )

    def perform_update(self, serializer):
        user = self.request.user
        question = serializer.instance

        if user.role not in ["INSTRUCTOR", "ADMIN"]:
            raise PermissionDenied(
                "Only instructors and admins can update questions."
            )

        if user.role != "ADMIN" and question.quiz.course.instructor != user:
            raise PermissionDenied(
                "You can only update questions for your own quizzes."
            )

        serializer.save()

    def perform_destroy(self, instance):
        user = self.request.user

        if user.role not in ["INSTRUCTOR", "ADMIN"]:
            raise PermissionDenied(
                "Only instructors and admins can delete questions."
            )

        if user.role != "ADMIN" and instance.quiz.course.instructor != user:
            raise PermissionDenied(
                "You can only delete questions for your own quizzes."
            )

        instance.delete()


# ============================================================
# OPTION MANAGEMENT
# ============================================================

class OptionListCreateView(generics.ListCreateAPIView):
    serializer_class = OptionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        question_id = self.request.query_params.get("question")

        if user.role == "ADMIN":
            qs = Option.objects.all()
        elif user.role == "INSTRUCTOR":
            qs = Option.objects.filter(question__quiz__course__instructor=user)
        else:
            qs = Option.objects.filter(
                question__quiz__is_published=True,
                question__quiz__course__is_published=True,
            )

        if question_id:
            qs = qs.filter(question_id=question_id)

        return qs

    def perform_create(self, serializer):
        user = self.request.user

        if user.role not in ["INSTRUCTOR", "ADMIN"]:
            raise PermissionDenied(
                "Only instructors and admins can create options."
            )

        question = serializer.validated_data["question"]

        if user.role != "ADMIN" and question.quiz.course.instructor != user:
            raise PermissionDenied(
                "You can only add options to your own quizzes."
            )

        serializer.save()


class OptionDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = OptionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if user.role == "ADMIN":
            return Option.objects.all()

        if user.role == "INSTRUCTOR":
            return Option.objects.filter(question__quiz__course__instructor=user)

        return Option.objects.filter(
            question__quiz__is_published=True,
            question__quiz__course__is_published=True,
        )

    def perform_update(self, serializer):
        user = self.request.user
        option = serializer.instance

        if user.role not in ["INSTRUCTOR", "ADMIN"]:
            raise PermissionDenied(
                "Only instructors and admins can update options."
            )

        if user.role != "ADMIN" and option.question.quiz.course.instructor != user:
            raise PermissionDenied(
                "You can only update options for your own quizzes."
            )

        serializer.save()

    def perform_destroy(self, instance):
        user = self.request.user

        if user.role not in ["INSTRUCTOR", "ADMIN"]:
            raise PermissionDenied(
                "Only instructors and admins can delete options."
            )

        if user.role != "ADMIN" and instance.question.quiz.course.instructor != user:
            raise PermissionDenied(
                "You can only delete options for your own quizzes."
            )

        instance.delete()


# ============================================================
# STUDENT QUIZ
# ============================================================

class StudentQuizDetailView(generics.RetrieveAPIView):
    serializer_class = StudentQuizSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if user.role == "ADMIN":
            return Quiz.objects.all()

        if user.role == "INSTRUCTOR":
            return Quiz.objects.filter(course__instructor=user)

        # For student: must be published quiz, published course, and student must be enrolled
        return Quiz.objects.filter(
            is_published=True,
            course__is_published=True,
            course__enrollments__student=user,
        ).distinct()


# ============================================================
# QUIZ SUBMISSION
# ============================================================

class QuizSubmitView(generics.CreateAPIView):
    serializer_class = QuizSubmissionSerializer
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        data = request.data.copy() if hasattr(request.data, "copy") else dict(request.data)
        if "quiz" not in data and "pk" in kwargs:
            data["quiz"] = kwargs["pk"]

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)

        student = request.user

        if student.role != "STUDENT":
            raise PermissionDenied(
                "Only students can submit quizzes."
            )

        quiz = serializer.validated_data["quiz"]
        answers = serializer.validated_data["answers"]

        # --------------------------------------------------------
        # Validate course and quiz publication & enrollment
        # --------------------------------------------------------
        if not quiz.is_published:
            raise PermissionDenied(
                "This quiz is not currently available."
            )

        if not quiz.course.is_published:
            raise PermissionDenied(
                "The course for this quiz is not published."
            )

        from enrollments.models import Enrollment

        if not Enrollment.objects.filter(
            student=student,
            course=quiz.course,
        ).exists():
            raise PermissionDenied(
                "You must be enrolled in this course to take this quiz."
            )

        # --------------------------------------------------------
        # Require all questions to be answered
        # --------------------------------------------------------
        total_questions = quiz.questions.count()

        if total_questions == 0:
            raise serializers.ValidationError(
                {"quiz": "This quiz does not have any questions."}
            )

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

        percentage = round((score / total_questions) * 100)
        is_passed = percentage >= quiz.passing_score

        # --------------------------------------------------------
        # Create quiz attempt
        # --------------------------------------------------------
        attempt = QuizAttempt.objects.create(
            student=student,
            quiz=quiz,
            score=score,
            total_questions=total_questions,
            percentage=percentage,
            is_passed=is_passed,
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
        status_text = "PASSED" if is_passed else "FAILED"
        Notification.objects.create(
            recipient=student,
            notification_type="QUIZ",
            title=f"Quiz {status_text}: {quiz.title}",
            message=(
                f"You scored {score}/{total_questions} ({percentage}%). "
                f"Status: {status_text} (Passing score: {quiz.passing_score}%)."
            ),
        )

        # --------------------------------------------------------
        # Response
        # --------------------------------------------------------
        return Response(
            {
                "message": f"Quiz submitted successfully. Result: {status_text}.",
                "attempt_id": attempt.id,
                "quiz": quiz.id,
                "score": score,
                "total_questions": total_questions,
                "percentage": percentage,
                "passing_score": quiz.passing_score,
                "is_passed": is_passed,
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

        if user.role == "ADMIN":
            return QuizAttempt.objects.select_related(
                "student",
                "quiz",
            ).order_by(
                "-submitted_at"
            )

        if user.role == "INSTRUCTOR":
            return QuizAttempt.objects.filter(
                quiz__course__instructor=user
            ).select_related(
                "student",
                "quiz",
            ).order_by(
                "-submitted_at"
            )

        raise PermissionDenied(
            "Only instructors and admins can view quiz attempts."
        )