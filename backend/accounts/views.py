from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .permissions import IsAdmin, IsInstructor, IsStudent
from .serializers import RegisterSerializer


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({
            "id": request.user.id,
            "username": request.user.username,
            "email": request.user.email,
            "role": request.user.role,
        })


class StudentTestView(APIView):
    permission_classes = [IsStudent]

    def get(self, request):
        return Response({
            "message": "Student access granted"
        })


class InstructorTestView(APIView):
    permission_classes = [IsInstructor]

    def get(self, request):
        return Response({
            "message": "Instructor access granted"
        })


class AdminTestView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        return Response({
            "message": "Admin access granted"
        }) 