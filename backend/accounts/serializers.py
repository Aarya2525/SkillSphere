from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        min_length=8
    )

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password",
        ]

    def create(self, validated_data):
        user = User.objects.create_user(
            password=validated_data.pop("password"),
            role=User.Role.STUDENT,
            **validated_data,
        )

        return user 