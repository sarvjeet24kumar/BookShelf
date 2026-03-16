import pytest
from tenants.serializers.tenant_serializers import TenantSerializer


@pytest.mark.django_db
class TestTenantSerializerUnit:
    """Unit tests for TenantSerializer validation."""

    def test_tenant_serializer_fields(self, tenant):
        """Test that fields are correctly serialized."""
        serializer = TenantSerializer(instance=tenant)
        data = serializer.data
        assert data["name"] == tenant.name
        assert data["slug"] == tenant.slug
        assert "subscription_plan" in data

    def test_read_only_fields(self, fake_data):
        """Test read-only fields for TenantSerializer."""
        data = {
            "id": 999,
            "name": fake_data.company(),
            "slug": fake_data.slug(),
            "created_at": "2021-01-01T00:00:00Z",
        }
        serializer = TenantSerializer(data=data)
        assert serializer.is_valid()
        assert "id" not in serializer.validated_data
        assert "created_at" not in serializer.validated_data
