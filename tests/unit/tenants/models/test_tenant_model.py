import pytest
from tenants.models import Tenant

@pytest.mark.django_db
class TestTenantModelUnit:
    """Unit tests for Tenant model."""

    def test_tenant_str(self, tenant_factory, fake_data):
        """Test the string representation of the tenant."""
        name = fake_data.company()
        tenant = tenant_factory.build(name=name)
        assert str(tenant) == name
