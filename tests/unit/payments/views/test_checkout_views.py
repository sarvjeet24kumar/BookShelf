"""Unit tests for CheckoutView."""

import pytest
from unittest.mock import patch, MagicMock
from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate
from payments.views.checkout_views import CheckoutView
from common.enums import SubscriptionStatus

@pytest.fixture
def checkout_view():
    return CheckoutView.as_view()

@pytest.fixture
def factory():
    return APIRequestFactory()

class TestCheckoutView:
    
    @patch("payments.views.checkout_views.Subscription")
    def test_checkout_no_tenant(self, MockSubscription, checkout_view, factory, mock_admin):
        """No tenant should return 403."""
        mock_admin.tenant = None
        
        request = factory.get("/api/v1/payments/checkout/")
        force_authenticate(request, user=mock_admin)
        
        with patch.object(CheckoutView, "check_permissions"):
            response = checkout_view(request)
            assert response.status_code == status.HTTP_403_FORBIDDEN
            assert "restricted to Tenant Admins" in str(response.data["detail"])

    @patch("payments.views.checkout_views.Subscription")
    def test_checkout_already_active(self, MockSubscription, checkout_view, factory, mock_admin):
        """Active subscription should return already_active template."""
        mock_sub = MagicMock()
        mock_sub.status = SubscriptionStatus.ACTIVE
        mock_sub.activated_at = "today"
        MockSubscription.objects.get_or_create.return_value = (mock_sub, False)
        
        request = factory.get("/api/v1/payments/checkout/")
        force_authenticate(request, user=mock_admin)
        
        with patch.object(CheckoutView, "check_permissions"):
            response = checkout_view(request)
            assert response.status_code == status.HTTP_200_OK
            assert response.template_name == "payments/already_active.html"

    @patch("payments.views.checkout_views.Subscription")
    @patch("payments.views.checkout_views.settings")
    def test_checkout_pending(self, mock_settings, MockSubscription, checkout_view, factory, mock_admin):
        """Pending subscription should return checkout template."""
        mock_settings.RAZORPAY_KEY_ID = "test_key"
        
        mock_sub = MagicMock()
        mock_sub.status = SubscriptionStatus.CREATED
        MockSubscription.objects.get_or_create.return_value = (mock_sub, True)
        
        request = factory.get("/api/v1/payments/checkout/")
        force_authenticate(request, user=mock_admin)
        
        with patch.object(CheckoutView, "check_permissions"):
            response = checkout_view(request)
            assert response.status_code == status.HTTP_200_OK
            assert response.template_name == "payments/checkout.html"
            assert response.data["RAZORPAY_KEY_ID"] == "test_key"
