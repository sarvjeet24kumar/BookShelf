"""Unit tests for CreateOrderView — all dependencies mocked."""
import pytest
from unittest.mock import patch, MagicMock
from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate
from payments.views.order_views import CreateOrderView
from common.enums import SubscriptionStatus


@pytest.fixture
def view():
    return CreateOrderView.as_view()


@pytest.fixture
def factory():
    return APIRequestFactory()


class TestCreateOrderView:
    """Unit tests for CreateOrderView.post()."""

    @patch("payments.views.order_views.PaymentOrderResponseSerializer")
    @patch("payments.views.order_views.Payment")
    @patch("payments.views.order_views.RazorpayService")
    @patch("payments.views.order_views.Subscription")
    def test_create_order_success(
        self, MockSubscription, MockRazorpay, MockPayment, MockSerializer,
        view, factory, mock_admin, fake_data
    ):
        """Admin with inactive subscription should create Razorpay order."""
        mock_sub = MagicMock()
        mock_sub.status = SubscriptionStatus.CREATED
        MockSubscription.objects.get_or_create.return_value = (mock_sub, True)

        order_id = f"order_{fake_data.msisdn()[:9]}"
        mock_rp = MockRazorpay.return_value
        mock_rp.create_order.return_value = {"id": order_id}

        mock_payment = MagicMock()
        mock_payment.razorpay_order_id = order_id
        mock_payment.amount = 50000
        mock_payment.currency = "INR"
        mock_payment.status = "created"
        MockPayment.objects.create.return_value = mock_payment

        mock_ser = MockSerializer.return_value
        mock_ser.data = {"razorpay_order_id": order_id}

        request = factory.post("/api/v1/payments/create-order/", {})
        force_authenticate(request, user=mock_admin)
        response = view(request)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["razorpay_order_id"] == order_id

    @patch("payments.views.order_views.Subscription")
    def test_create_order_already_active_subscription(
        self, MockSubscription, view, factory, mock_admin
    ):
        """Tenant with active subscription should get 400."""
        mock_sub = MagicMock()
        mock_sub.status = SubscriptionStatus.ACTIVE
        MockSubscription.objects.get_or_create.return_value = (mock_sub, False)

        request = factory.post("/api/v1/payments/create-order/", {})
        force_authenticate(request, user=mock_admin)
        response = view(request)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "active lifetime subscription" in str(response.data["error"]["details"])

    def test_create_order_no_tenant(self, view, factory):
        """User without tenant should get 403 (permission denied by IsTenantAdmin)."""
        from tests.unit.conftest import _make_mock_user
        from common.enums import UserRole
        no_tenant_user = _make_mock_user(role=UserRole.ADMIN, tenant=None)

        request = factory.post("/api/v1/payments/create-order/", {})
        force_authenticate(request, user=no_tenant_user)
        response = view(request)
        assert response.status_code == status.HTTP_403_FORBIDDEN
