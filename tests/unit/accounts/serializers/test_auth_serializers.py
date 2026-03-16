import pytest
from accounts.serializers.auth_serializers import SignupSerializer, LoginSerializer, ChangePasswordSerializer
from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()

@pytest.mark.django_db
class TestSignupSerializerUnit:
    """Unit tests for SignupSerializer validation logic."""

    def test_passwords_match_validation(self, fake_data):
        """Test that mismatched passwords raise ValidationError."""
        data = {
            "username": fake_data.user_name(),
            "email": fake_data.email(),
            "password": fake_data.password(special_chars=True),
            "password_confirm": "Mismatched@123",
            "first_name": fake_data.first_name(),
            "last_name": fake_data.last_name(),
            "phone_no": f"+91{fake_data.msisdn()[:10]}"
        }
        serializer = SignupSerializer(data=data)
        assert not serializer.is_valid()
        assert "Passwords don't match" in str(serializer.errors.get("non_field_errors", []))

    def test_duplicate_username_validation(self, user_factory, fake_data):
        """Test that duplicate username raises ValidationError."""
        username = fake_data.user_name()
        user_factory(username=username)
        password = fake_data.password()
        data = {
            "username": username,
            "email": fake_data.email(),
            "password": password,
            "password_confirm": password,
            "first_name": fake_data.first_name(),
            "last_name": fake_data.last_name(),
            "phone_no": f"+91{fake_data.msisdn()[:10]}"
        }
        serializer = SignupSerializer(data=data)
        assert not serializer.is_valid()
        assert "username already exists" in str(serializer.errors.get("username", []))


class TestLoginSerializerUnit:
    """Unit tests for LoginSerializer validation logic."""

    def test_both_email_and_username_fails(self, fake_data):
        """Test providing both email and username raises ValidationError."""
        data = {
            "email": fake_data.email(),
            "username": fake_data.user_name(),
            "password": fake_data.password()
        }
        serializer = LoginSerializer(data=data)
        assert not serializer.is_valid()
        assert "Provide either email or username, not both" in str(serializer.errors.get("non_field_errors", []))

    def test_neither_email_nor_username_fails(self, fake_data):
        """Test providing neither email nor username raises ValidationError."""
        data = {"password": fake_data.password()}
        serializer = LoginSerializer(data=data)
        assert not serializer.is_valid()
        assert "Email or username is required" in str(serializer.errors.get("non_field_errors", []))


class TestChangePasswordSerializerUnit:
    """Unit tests for ChangePasswordSerializer validation logic."""

    def test_mismatched_new_passwords(self, fake_data):
        """Test that mismatched new passwords raise ValidationError."""
        data = {
            "current_password": "OldPassword123!",
            "new_password": "NewPassword123!",
            "confirm_password": "Mismatched@123"
        }
        serializer = ChangePasswordSerializer(data=data)
        assert not serializer.is_valid()
        assert "New passwords don't match" in str(serializer.errors.get("confirm_password", []))

    def test_new_password_same_as_current(self, fake_data):
        """Test that new password same as current raises ValidationError."""
        # Ensure password has a special char from the restricted set [!@#$%^&*]
        password = "Password123!"
        data = {
            "current_password": password,
            "new_password": password,
            "confirm_password": password
        }
        serializer = ChangePasswordSerializer(data=data)
        assert not serializer.is_valid()
        assert "must be different from current password" in str(serializer.errors.get("new_password", []))
