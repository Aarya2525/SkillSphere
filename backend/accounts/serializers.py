from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

User = get_user_model()


ALLOWED_REGISTRATION_ROLES = (
    User.Role.STUDENT,
    User.Role.INSTRUCTOR,
)


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        min_length=8
    )
    role = serializers.ChoiceField(
        choices=ALLOWED_REGISTRATION_ROLES,
        default=User.Role.STUDENT,
        required=False,
    )

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password",
            "role",
        ]

    def validate_password(self, value):
        try:
            validate_password(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages))
        return value

    def validate_role(self, value):
        if value not in ALLOWED_REGISTRATION_ROLES:
            raise serializers.ValidationError(
                "Role must be either STUDENT or INSTRUCTOR."
            )
        return value

    def create(self, validated_data):
        role = validated_data.pop("role", User.Role.STUDENT)
        user = User.objects.create_user(
            password=validated_data.pop("password"),
            role=role,
            **validated_data,
        )

        return user
