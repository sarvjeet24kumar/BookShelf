"""Unit tests for TenantListCreateView and TenantDetailView ."""

import pytest
import uuid
from unittest.mock import patch, MagicMock
from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate
from tenants.models import Tenant as RealTenant
from tenants.views.tenant_views import TenantListCreateView, TenantDetailView
from common.enums import UserRole


@pytest.fixture
def list_view():
    return TenantListCreateView.as_view()


@pytest.fixture
def detail_view():
    return TenantDetailView.as_view()


@pytest.fixture
def factory():
    return APIRequestFactory()


class TestTenantListCreateView:
    """Unit tests for TenantListCreateView."""

    @patch("tenants.views.tenant_views.Tenant")
    @patch("tenants.views.tenant_views.TenantSerializer")
    def test_list_tenants_as_superadmin(
        self, MockSerializer, MockTenant, list_view, factory, mock_super_admin
    ):
        """Super admin should see all tenants."""
        mock_qs = MagicMock()
        mock_qs.order_by.return_value = []
        MockTenant.all_objects.all.return_value = mock_qs

        mock_ser = MockSerializer.return_value
        mock_ser.data = []

        request = factory.get("/api/v1/tenants/")
        force_authenticate(request, user=mock_super_admin)
        response = list_view(request)
        assert response.status_code == status.HTTP_200_OK
        # Handle both direct list and paginated dict response
        if isinstance(response.data, dict):
            assert "data" in response.data
            assert isinstance(response.data["data"], list)
        else:
            assert isinstance(response.data, list)

    @patch("tenants.views.tenant_views.Tenant")
    @patch("tenants.views.tenant_views.TenantSerializer")
    def test_list_tenants_as_admin_sees_own(
        self, MockSerializer, MockTenant, list_view, factory, mock_admin
    ):
        """Admin should see only their own tenant."""
        mock_qs = MagicMock()
        MockTenant.all_objects.filter.return_value = mock_qs

        mock_ser = MockSerializer.return_value
        mock_ser.data = []

        request = factory.get("/api/v1/tenants/")
        force_authenticate(request, user=mock_admin)
        response = list_view(request)
        assert response.status_code == status.HTTP_200_OK
        assert "data" in response.data
        assert isinstance(response.data["data"], list)

    @patch("tenants.views.tenant_views.TenantCreateSerializer")
    @patch("tenants.views.tenant_views.TenantSerializer")
    def test_create_tenant_as_superadmin(
        self, MockSer, MockCreateSer, list_view, factory, mock_super_admin, fake_data
    ):
        """Super admin should create a tenant and get 201."""
        tenant_name = fake_data.company()
        tenant_slug = fake_data.slug()
        mock_create_ser = MockCreateSer.return_value
        mock_create_ser.is_valid.return_value = True
        mock_tenant = MagicMock()
        mock_tenant.slug = tenant_slug
        mock_create_ser.save.return_value = mock_tenant

        mock_response_ser = MockSer.return_value
        mock_data = {"name": tenant_name, "slug": tenant_slug}
        mock_response_ser.data = mock_data

        request = factory.post(
            "/api/v1/tenants/", {"name": tenant_name, "slug": tenant_slug}
        )
        force_authenticate(request, user=mock_super_admin)
        response = list_view(request)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data == mock_data


class TestTenantDetailView:
    """Unit tests for TenantDetailView."""

    @patch("tenants.views.tenant_views.Tenant")
    @patch("tenants.views.tenant_views.TenantDetailSerializer")
    def test_get_tenant_as_superadmin(
        self,
        MockSerializer,
        MockTenant,
        detail_view,
        factory,
        mock_super_admin,
        fake_data,
    ):
        """Super admin should retrieve any tenant."""
        mock_t = MagicMock()
        MockTenant.all_objects.get.return_value = mock_t

        mock_ser = MockSerializer.return_value
        mock_data = {"name": fake_data.company()}
        mock_ser.data = mock_data

        tenant_id = str(fake_data.random_int())
        request = factory.get(f"/api/v1/tenants/{tenant_id}/")
        force_authenticate(request, user=mock_super_admin)
        response = detail_view(request, id=tenant_id)
        assert response.status_code == status.HTTP_200_OK
        assert response.data == mock_data

    @patch("tenants.views.tenant_views.Tenant")
    def test_get_tenant_not_found(
        self, MockTenant, detail_view, factory, mock_super_admin, fake_data
    ):
        """Non-existent tenant should return 404."""

        MockTenant.DoesNotExist = RealTenant.DoesNotExist
        MockTenant.all_objects.get.side_effect = RealTenant.DoesNotExist

        tenant_id = str(fake_data.random_int())
        request = factory.get(f"/api/v1/tenants/{tenant_id}/")
        force_authenticate(request, user=mock_super_admin)
        response = detail_view(request, id=tenant_id)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data["error"]["message"] == "Tenant not found."

    def test_tenant_admin_cannot_access_other_tenant(
        self, detail_view, factory, mock_admin, fake_data
    ):
        """Admin should get 403 when accessing another tenant."""
        other_tenant = MagicMock()
        other_tenant.id = str(fake_data.uuid4())
        mock_admin.tenant_id = str(fake_data.uuid4())

        with patch(
            "tenants.views.tenant_views.TenantListCreateView.get_permissions",
            return_value=[],
        ):
            with patch(
                "tenants.views.tenant_views.Tenant.all_objects.get",
                return_value=other_tenant,
            ):
                request = factory.get(f"/api/v1/tenants/{other_tenant.id}/")
                force_authenticate(request, user=mock_admin)
                response = detail_view(request, id=other_tenant.id)
                assert response.status_code == status.HTTP_403_FORBIDDEN
                assert (
                    response.data["error"]["message"]
                    == "You can only access your own tenant."
                )

    @patch("tenants.views.tenant_views.Tenant")
    def test_delete_tenant_as_superadmin(
        self, MockTenant, detail_view, factory, mock_super_admin, fake_data
    ):
        """Super admin should delete tenant and return 204."""
        mock_t = MagicMock()
        MockTenant.all_objects.get.return_value = mock_t

        tenant_id = str(fake_data.random_int())
        request = factory.delete(f"/api/v1/tenants/{tenant_id}/")
        force_authenticate(request, user=mock_super_admin)
        response = detail_view(request, id=tenant_id)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        mock_t.soft_delete.assert_called_once()
