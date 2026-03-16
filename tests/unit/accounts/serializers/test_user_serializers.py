import pytest
from accounts.serializers.user_serializers import UserSerializer, UserDetailSerializer
from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()

@pytest.mark.django_db
class TestUserSerializerUnit:
    """Unit tests for UserSerializer validation logic."""

    def test_duplicate_username_fails(self, user_factory, fake_data):
        """Test that duplicate username raises ValidationError in UserSerializer."""
        username = fake_data.user_name()
        user_factory(username=username)
        data = {
            "username": username,
            "email": fake_data.email(),
            "password": fake_data.password(special_chars=True),
            "first_name": fake_data.first_name(),
            "last_name": fake_data.last_name(),
            "phone_no": f"+91{fake_data.msisdn()[:10]}"
        }
        serializer = UserSerializer(data=data)
        assert not serializer.is_valid()
        assert "username already exists" in str(serializer.errors.get("username", []))

    def test_read_only_fields(self, fake_data):
        """Test read-only fields are not updated."""
        data = {
            "id": 999,
            "username": fake_data.user_name(),
            "email": fake_data.email(),
            "password": fake_data.password(special_chars=True),
            "first_name": fake_data.first_name(),
            "last_name": fake_data.last_name(),
            "phone_no": f"+91{fake_data.msisdn()[:10]}",
            "created_at": "2021-01-01T00:00:00Z"
        }
        serializer = UserSerializer(data=data)
        assert serializer.is_valid()
        # id and created_at should not be in validated_data
        assert "id" not in serializer.validated_data
        assert "created_at" not in serializer.validated_data


@pytest.mark.django_db
class TestUserDetailSerializerUnit:
    """Unit tests for UserDetailSerializer updates."""

    def test_username_update_duplicate_fails(self, user, user_factory, fake_data):
        """Test updating username to an existing one fails."""
        other_username = fake_data.user_name()
        user_factory(username=other_username)
        data = {"username": other_username}
        serializer = UserDetailSerializer(instance=user, data=data, partial=True)
        assert not serializer.is_valid()
        assert "username already exists" in str(serializer.errors.get("username", []))

    def test_username_update_same_user_success(self, user):
        """Test updating to same username succeeds for current user."""
        data = {"username": user.username}
        serializer = UserDetailSerializer(instance=user, data=data, partial=True)
        assert serializer.is_valid()

    def test_password_update_hashing(self, user, fake_data):
        """Test that updating password via serializer hashes it."""
        old_password_hash = user.password
        new_password = fake_data.password(length=12)
        data = {"password": new_password}
        serializer = UserDetailSerializer(instance=user, data=data, partial=True)
        assert serializer.is_valid()
        updated_user = serializer.save()
        assert updated_user.password != old_password_hash
        assert updated_user.check_password(new_password)
