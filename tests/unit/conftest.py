"""Shared unit test conftest — mock request, fake data, mock users."""

import uuid
import pytest
from unittest.mock import MagicMock, PropertyMock
from faker import Faker
from rest_framework.test import APIRequestFactory
from django.conf import settings
from pytest_factoryboy import register
from tests.factories.account_factories import TenantFactory, UserFactory
from tests.factories.book_factories import BookFactory, GenreFactory, UserBookFactory
from tests.factories.payment_factories import SubscriptionFactory, PaymentFactory
from common.enums import UserRole

# 

# Disable throttling for tests
if hasattr(settings, "REST_FRAMEWORK"):
    settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {
        "anon": None,
        "user": None,
        "ip_throttle": None,
        "auth_throttle": None,
    }

# Register factories
register(TenantFactory)
register(UserFactory)
register(GenreFactory)
register(BookFactory)
register(SubscriptionFactory)
register(PaymentFactory)
register(UserBookFactory)
fake = Faker()


@pytest.fixture
def fake_data():
    """Provide a Faker instance."""
    return fake


@pytest.fixture
def api_factory():
    """DRF APIRequestFactory for building requests without routing."""
    return APIRequestFactory()


def _make_mock_user(role=UserRole.USER, tenant=None, **overrides):
    """Create a MagicMock user with sensible defaults."""
    user = MagicMock()
    user.id = uuid.uuid4()
    user.username = fake.user_name()
    user.email = fake.email()
    user.first_name = fake.first_name()
    user.last_name = fake.last_name()
    user.phone_no = f"+91{fake.msisdn()[:10]}"
    user.role = role
    user.is_active = True
    user.is_email_verified = True
    user.deleted_at = None
    user.tenant = tenant
    user.tenant_id = tenant.id if tenant else None
    user.check_password = MagicMock(return_value=True)
    user.set_password = MagicMock()
    user.save = MagicMock()
    user.soft_delete = MagicMock()
    user.refresh_from_db = MagicMock()
    # Apply overrides
    for k, v in overrides.items():
        setattr(user, k, v)
    return user


def _make_mock_tenant():
    """Create a MagicMock tenant."""
    tenant = MagicMock()
    tenant.id = uuid.uuid4()
    tenant.name = fake.company()
    tenant.slug = fake.slug()
    tenant.is_active = True
    tenant.deleted_at = None
    return tenant


@pytest.fixture
def mock_tenant():
    return _make_mock_tenant()


@pytest.fixture
def mock_user(mock_tenant):
    return _make_mock_user(tenant=mock_tenant)


@pytest.fixture
def mock_admin(mock_tenant):
    return _make_mock_user(role=UserRole.ADMIN, tenant=mock_tenant)


@pytest.fixture
def mock_super_admin():
    return _make_mock_user(role=UserRole.SUPER_ADMIN, tenant=None)
