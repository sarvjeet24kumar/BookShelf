import pytest
from django.db import IntegrityError
from common.enums import SubscriptionPlan
from tenants.models import Tenant


@pytest.mark.django_db
class TestTenantModelUnit:
    """Unit tests for Tenant model."""

    def test_tenant_str(self, tenant_factory, fake_data):
        """Test the string representation of the tenant."""
        name = fake_data.company()
        tenant = tenant_factory.build(name=name)
        assert str(tenant) == name

    def test_tenant_creation(self, tenant_factory, fake_data):
        """Tenant is created with correct field values."""
        name = fake_data.company()
        slug = fake_data.slug()
        tenant = tenant_factory.create(name=name, slug=slug, is_active=True)
        assert tenant.name == name
        assert tenant.slug == slug
        assert tenant.is_active is True

    def test_slug_uniqueness(self, tenant_factory, fake_data):
        """Duplicate slugs raise an IntegrityError."""

        slug = fake_data.slug()
        tenant_factory.create(slug=slug)
        with pytest.raises(IntegrityError):
            tenant_factory.create(slug=slug)

    def test_default_subscription_plan(self, tenant_factory):
        """Test that the default subscription plan is FREE."""

        tenant = tenant_factory.create()
        assert tenant.subscription_plan == SubscriptionPlan.FREE
