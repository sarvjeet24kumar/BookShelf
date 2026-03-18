import pytest
from django.urls import reverse
from rest_framework import status
from tenants.models import Tenant
from tests.factories.account_factories import TenantFactory

@pytest.mark.django_db
class TestTenantViews:
    """ Integration tests for Tenants. """

    def test_tenant_list(self, api_client, super_admin, tenant):
        api_client.force_authenticate(user=super_admin)
        url = reverse("tenant-list-create")
        response = api_client.get(url, HTTP_TENANT_ID=str(tenant.id))
        assert response.status_code == status.HTTP_200_OK

    def test_tenant_create(self, api_client, super_admin, tenant, faker):
        api_client.force_authenticate(user=super_admin)
        url = reverse("tenant-list-create")
        slug = faker.unique.slug()
        data = {"name": faker.company(), "slug": slug}
        response = api_client.post(url, data, HTTP_TENANT_ID=str(tenant.id))
        assert response.status_code == status.HTTP_201_CREATED

    def test_tenant_update(self, api_client, super_admin, tenant, faker):
        api_client.force_authenticate(user=super_admin)
        url = reverse("tenant-detail", kwargs={"id": tenant.id})
        name = faker.company()
        response = api_client.patch(url, {"name": name}, HTTP_TENANT_ID=str(tenant.id))
        assert response.status_code == status.HTTP_200_OK
        tenant.refresh_from_db()
        assert tenant.name == name

    def test_tenant_delete(self, api_client, super_admin, tenant):
        api_client.force_authenticate(user=super_admin)
        target = TenantFactory()
        url = reverse("tenant-detail", kwargs={"id": target.id})
        response = api_client.delete(url, HTTP_TENANT_ID=str(tenant.id))
        assert response.status_code == status.HTTP_204_NO_CONTENT
