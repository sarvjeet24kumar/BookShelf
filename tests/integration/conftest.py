import pytest
from tenants.models import Tenant
from common.enums import UserRole
from django.conf import settings
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from pytest_factoryboy import register
from tests.factories.account_factories import TenantFactory, UserFactory
from tests.factories.book_factories import BookFactory, GenreFactory, UserBookFactory
from tests.factories.payment_factories import SubscriptionFactory, PaymentFactory

User = get_user_model()

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


@pytest.fixture
def api_client():
    """Fixture for DRF API client."""
    return APIClient()


@pytest.fixture
def admin_user(user_factory, tenant):
    """Fixture for an admin user using FactoryBoy traits."""
    return user_factory(tenant=tenant, is_admin=True)


@pytest.fixture
def super_admin(user_factory):
    """Fixture for a super admin using FactoryBoy traits."""
    return user_factory(is_super_admin=True)


@pytest.fixture
def user(user_factory, tenant):
    """Override default user to ensure it's attached to the default tenant."""
    return user_factory(tenant=tenant)


@pytest.fixture
def subscription(subscription_factory, tenant):
    """Override default subscription to attach to default tenant."""
    from tenants.models import Tenant

    try:
        if tenant.subscription:
            return tenant.subscription
    except Tenant.subscription.RelatedObjectDoesNotExist:
        pass
    return subscription_factory(tenant=tenant)


@pytest.fixture
def genre(genre_factory, tenant):
    return genre_factory(tenant=tenant)


@pytest.fixture
def book(book_factory, tenant, user, genre):
    return book_factory(tenant=tenant, created_by=user, genres=[genre])


@pytest.fixture
def payment(payment_factory, user, subscription):
    return payment_factory(subscription=subscription, initiated_by=user)
