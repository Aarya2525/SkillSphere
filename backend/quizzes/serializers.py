from rest_framework import serializers

from .models import (
    Answer,
    Option,
    Question,
    Quiz,
    QuizAttempt,
)


class OptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Option
        fields = [
            "id",
            "question",
            "text",
            "is_correct",
        ]


class QuestionSerializer(serializers.ModelSerializer):
    options = OptionSerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = Question
        fields = [
            "id",
            "quiz",
            "text",
            "order",
            "options",
        ]


class QuizSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(
        many=True,
        read_only=True,
    )
    course_title = serializers.CharField(
        source="course.title",
        read_only=True,
    )

    def validate_passing_score(self, value):
        if value < 1 or value > 100:
            raise serializers.ValidationError(
                "Passing score must be between 1 and 100."
            )
        return value

    class Meta:
        model = Quiz
        fields = [
            "id",
            "course",
            "course_title",
            "title",
            "description",
            "passing_score",
            "is_published",
            "questions",
        ]


# ============================================================
# STUDENT-FACING SERIALIZERS
# ============================================================

class StudentOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Option
        fields = [
            "id",
            "question",
            "text",
        ]


class StudentQuestionSerializer(serializers.ModelSerializer):
    options = StudentOptionSerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = Question
        fields = [
            "id",
            "quiz",
            "text",
            "order",
            "options",
        ]


class StudentQuizSerializer(serializers.ModelSerializer):
    questions = StudentQuestionSerializer(
        many=True,
        read_only=True,
    )
    course_title = serializers.CharField(
        source="course.title",
        read_only=True,
    )

    class Meta:
        model = Quiz
        fields = [
            "id",
            "course",
            "course_title",
            "title",
            "description",
            "passing_score",
            "questions",
        ]
        read_only_fields = [
            "id",
            "course",
            "course_title",
            "title",
            "description",
            "passing_score",
            "questions",
        ]


# ============================================================
# ANSWER SERIALIZER
# ============================================================

class AnswerSerializer(serializers.ModelSerializer):
    question_text = serializers.CharField(
        source="question.text",
        read_only=True,
    )

    selected_option_text = serializers.CharField(
        source="selected_option.text",
        read_only=True,
    )

    is_correct = serializers.SerializerMethodField()

    correct_option_text = serializers.SerializerMethodField()

    def get_is_correct(self, obj):
        return obj.selected_option.is_correct

    def get_correct_option_text(self, obj):
        correct_option = obj.question.options.filter(
            is_correct=True
        ).first()

        if correct_option:
            return correct_option.text

        return None

    class Meta:
        model = Answer
        fields = [
            "id",
            "attempt",
            "question",
            "question_text",
            "selected_option",
            "selected_option_text",
            "is_correct",
            "correct_option_text",
        ]

        read_only_fields = [
            "attempt",
            "question_text",
            "selected_option_text",
            "is_correct",
            "correct_option_text",
        ]


# ============================================================
# QUIZ ATTEMPT SERIALIZER
# ============================================================

class QuizAttemptSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(
        source="student.username",
        read_only=True,
    )

    quiz_title = serializers.CharField(
        source="quiz.title",
        read_only=True,
    )

    passing_score = serializers.IntegerField(
        source="quiz.passing_score",
        read_only=True,
    )

    answers = AnswerSerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = QuizAttempt
        fields = [
            "id",
            "student",
            "student_name",
            "quiz",
            "quiz_title",
            "score",
            "total_questions",
            "percentage",
            "is_passed",
            "passing_score",
            "submitted_at",
            "answers",
        ]

        read_only_fields = [
            "student",
            "student_name",
            "score",
            "total_questions",
            "percentage",
            "is_passed",
            "passing_score",
            "submitted_at",
            "answers",
        ]


# ============================================================
# QUIZ SUBMISSION SERIALIZER
# ============================================================

class QuizSubmissionSerializer(serializers.Serializer):
    quiz = serializers.PrimaryKeyRelatedField(
        queryset=Quiz.objects.all()
    )

    answers = serializers.ListField(
        child=serializers.DictField(),
        allow_empty=False,
    )

    def validate(self, attrs):
        quiz = attrs["quiz"]
        answers = attrs["answers"]

        if not answers:
            raise serializers.ValidationError(
                "At least one answer is required."
            )

        question_ids = set()
        validated_answers = []

        for answer in answers:
            if "question" not in answer:
                raise serializers.ValidationError(
                    "Each answer must contain a question."
                )

            if "selected_option" not in answer:
                raise serializers.ValidationError(
                    "Each answer must contain a selected_option."
                )

            question_id = answer["question"]
            option_id = answer["selected_option"]

            if not isinstance(question_id, int):
                raise serializers.ValidationError(
                    "Question ID must be an integer."
                )

            if not isinstance(option_id, int):
                raise serializers.ValidationError(
                    "Selected option ID must be an integer."
                )

            if question_id in question_ids:
                raise serializers.ValidationError(
                    f"Question {question_id} was answered more than once."
                )

            question_ids.add(question_id)

            try:
                question = quiz.questions.get(
                    id=question_id
                )
            except Question.DoesNotExist:
                raise serializers.ValidationError(
                    f"Question {question_id} does not belong to this quiz."
                )

            try:
                option = question.options.get(
                    id=option_id
                )
            except Option.DoesNotExist:
                raise serializers.ValidationError(
                    f"Option {option_id} does not belong to question {question_id}."
                )

            validated_answers.append(
                {
                    "question": question,
                    "selected_option": option,
                }
            )

        attrs["answers"] = validated_answers

        return attrs


# ============================================================
# INSTRUCTOR / ADMIN ATTEMPT SERIALIZER
# ============================================================

class InstructorQuizAttemptSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(
        source="student.username",
        read_only=True,
    )

    quiz_title = serializers.CharField(
        source="quiz.title",
        read_only=True,
    )

    passing_score = serializers.IntegerField(
        source="quiz.passing_score",
        read_only=True,
    )

    class Meta:
        model = QuizAttempt
        fields = [
            "id",
            "student",
            "student_name",
            "quiz",
            "quiz_title",
            "score",
            "total_questions",
            "percentage",
            "is_passed",
            "passing_score",
            "submitted_at",
        ]

        read_only_fields = [
            "id",
            "student",
            "student_name",
            "quiz",
            "quiz_title",
            "score",
            "total_questions",
            "percentage",
            "is_passed",
            "passing_score",
            "submitted_at",
        ] 