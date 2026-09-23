"""
API views for the AI Learning Assistant app.
Hardened with role access controls, context safety boundaries, and rate throttling for Stage 15.
"""
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from courses.models import Lesson
from enrollments.models import Enrollment
from .providers.base import (
    AIConfigurationError,
    AIProviderError,
    AITimeoutError,
)
from .serializers import (
    AIAssistantAskRequestSerializer,
    AIAssistantAskResponseSerializer,
)
from .services import ask_tutor
from .throttling import AIAssistantRateThrottle


class AIAssistantAskView(APIView):
    """
    POST /api/ai/ask/
    Allows authenticated students enrolled in a published course (or authorized instructors/admins)
    to ask contextual questions about a specific lesson to the AI Learning Assistant.
    Enforces per-user rate throttling, RBAC, and error sanitization.
    """
    permission_classes = [IsAuthenticated]
    throttle_classes = [AIAssistantRateThrottle]

    def post(self, request):
        serializer = AIAssistantAskRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        lesson_id = serializer.validated_data["lesson_id"]
        message = serializer.validated_data["message"]

        # Retrieve lesson with course hierarchy
        lesson = (
            Lesson.objects.select_related("module__course__instructor")
            .filter(id=lesson_id)
            .first()
        )

        if not lesson:
            return Response(
                {"error": "Lesson not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        course = lesson.module.course
        user = request.user

        # Access control enforcement
        if user.role == "STUDENT":
            if not course.is_published:
                return Response(
                    {"error": "You can only access lessons from published courses."},
                    status=status.HTTP_403_FORBIDDEN,
                )

            is_enrolled = Enrollment.objects.filter(
                student=user,
                course=course,
            ).exists()

            if not is_enrolled:
                return Response(
                    {"error": "You must be enrolled in this course to use the AI assistant."},
                    status=status.HTTP_403_FORBIDDEN,
                )

        elif user.role == "INSTRUCTOR":
            if course.instructor != user:
                return Response(
                    {"error": "You do not have access to this course."},
                    status=status.HTTP_403_FORBIDDEN,
                )

        # Call AI tutor service with safety handling
        try:
            answer = ask_tutor(lesson, message)
        except AIConfigurationError:
            return Response(
                {"error": "AI assistant is currently not configured on the server."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except AITimeoutError:
            return Response(
                {"error": "AI assistant timed out waiting for a response. Please try again."},
                status=status.HTTP_504_GATEWAY_TIMEOUT,
            )
        except AIProviderError:
            return Response(
                {"error": "AI assistant encountered an error generating a response."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        response_serializer = AIAssistantAskResponseSerializer(
            data={"answer": answer, "lesson_id": lesson.id}
        )
        response_serializer.is_valid()
        return Response(
            response_serializer.data,
            status=status.HTTP_200_OK,
        )
