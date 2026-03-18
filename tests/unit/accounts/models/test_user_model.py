import pytest
from django.db import IntegrityError
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from common.enums import UserRole

User = get_user_model()


@pytest.mark.django_db
class TestUserModelUnit:
    """Unit tests for User model focus on logic and validators."""

    def test_user_str(self, user_factory, fake_data):
        """Test the string representation of the user."""
        username = fake_data.user_name()
        user = user_factory.build(username=username)
        assert str(user) == username

    def test_user_creation(self, user_factory, tenant, fake_data):
        """User is created with correct field values."""
        username = fake_data.user_name()
        email = fake_data.email()
        first_name = fake_data.first_name()
        user = user_factory.create(
            username=username,
            email=email,
            first_name=first_name,
            tenant=tenant,
            is_email_verified=True,
        )
        assert user.username == username
        assert user.email == email
        assert user.first_name == first_name
        assert user.tenant == tenant
        assert user.is_email_verified is True

    def test_email_tenant_uniqueness(self, user_factory, tenant, fake_data):
        """Duplicate emails within the same tenant raise an IntegrityError."""

        email = fake_data.email()
        user_factory.create(email=email, tenant=tenant)
        with pytest.raises(IntegrityError):
            user_factory.create(email=email, tenant=tenant)

    def test_user_default_role(self, user_factory):
        """Test that the default role is USER."""
        user = user_factory.build()
        assert user.role == UserRole.USER

    def test_invalid_username_validator(self, user_factory, fake_data):
        """Test that invalid usernames raise ValidationError."""
        # Using build() + full_clean() is more "unit" than create()
        user = user_factory.build(username=fake_data.lexify('????'))  # Too short
        with pytest.raises(ValidationError):
            user.full_clean()

    def test_invalid_phone_validator(self, user_factory):
        """Test that invalid phone numbers raise ValidationError."""
        user = user_factory.build(phone_no="invalid")
        with pytest.raises(ValidationError):
            user.full_clean()

    def test_valid_user_clean(self, user_factory, tenant, fake_data):
        """Test that a valid user passes full_clean."""
        user = user_factory.build(
            username=fake_data.user_name(),
            email=fake_data.email(),
            phone_no=f"+91{fake_data.msisdn()[:10]}",
            tenant=tenant,
        )
        # Should not raise
        user.full_clean()
