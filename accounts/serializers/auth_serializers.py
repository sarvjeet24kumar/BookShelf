from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth import authenticate, get_user_model
from common.validators import validate_password
from accounts.constants import MIN_PASSWORD_LENGTH
from common.validators import username_validator
from django.core.exceptions import ValidationError as DjangoValidationError
from accounts.services import email_verification_service
from common.enums import UserRole

User = get_user_model()
import logging

logger = logging.getLogger(__name__)


class SignupSerializer(serializers.ModelSerializer):
    """
    Serializer for user signup.
    """

    password_confirm = serializers.CharField(
        write_only=True, min_length=MIN_PASSWORD_LENGTH
    )

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "password",
            "password_confirm",
            "first_name",
            "last_name",
            "phone_no",
        )
        extra_kwargs = {
            "password": {"write_only": True},
            "username": {"validators": []},
            "email": {"validators": []},
        }

    def validate_username(self, value):
        """Validate username is not already taken."""
        username = value.lower()
        if User.all_objects.filter(username=username).exists():
            raise serializers.ValidationError(
                "user with this username already exists."
            )
        return username

    def validate_email(self, value):
        return value.lower()

    def validate_password(self, value):
        validate_password(value.strip())
        return value.strip()

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError("Passwords don't match.")
        attrs.pop("password_confirm")
        return attrs

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class VerifyEmailSerializer(serializers.Serializer):
    """Serializer for email verification with OTP."""

    email = serializers.EmailField()
    otp = serializers.CharField(min_length=6, max_length=6)

    def validate_email(self, value):
        return value.strip().lower()

    def validate_otp(self, value):
        return value.strip()


class LoginSerializer(serializers.Serializer):
    """Serializer for user login."""

    email = serializers.EmailField(required=False)
    username = serializers.CharField(required=False)
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get("email", "").lower()
        username = attrs.get("username", "").lower()
        password = attrs.get("password", "").strip()

        if email and username:
            raise serializers.ValidationError("Provide either email or username, not both.")
        if not email and not username:
            raise serializers.ValidationError("Email or username is required.")
        if not password:
            raise serializers.ValidationError("Password is required.")

        attrs["email"] = email if email else None
        attrs["username"] = username if username else None
        attrs["password"] = password
        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing password for authenticated users."""
    
    current_password = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(write_only=True, required=True, min_length=MIN_PASSWORD_LENGTH)
    confirm_password = serializers.CharField(write_only=True, required=True, min_length=MIN_PASSWORD_LENGTH)
    
    def validate_new_password(self, value):
        """Validate new password meets requirements."""
        validate_password(value.strip())
        return value.strip()
    
    def validate(self, attrs):
        """Validate passwords match and new password is different from current."""
        current_password = attrs.get('current_password', '').strip()
        new_password = attrs.get('new_password', '').strip()
        confirm_password = attrs.get('confirm_password', '').strip()
        
        if new_password != confirm_password:
            raise serializers.ValidationError({"confirm_password": "New passwords don't match."})
        
        if current_password == new_password:
            raise serializers.ValidationError({"new_password": "New password must be different from current password."})
        
        return attrs
