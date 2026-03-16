"""Unit tests for VerifyPaymentView — all dependencies mocked."""
import pytest
from unittest.mock import patch, MagicMock
from rest_framework import status
from rest_framework.test import APIRequestFactory
from payments.views.verification_views import VerifyPaymentView
from common.enums import PaymentStatus


@pytest.fixture
def view():
    return VerifyPaymentView.as_view()


@pytest.fixture
def factory():
    return APIRequestFactory()


class TestVerifyPaymentView:
    """Unit tests for VerifyPaymentView.post()."""

    def test_verify_missing_fields(self, view, factory, fake_data):
        """Missing required fields should return 400."""
        request = factory.post("/api/v1/payments/verify/", {"razorpay_order_id": f"order_{fake_data.msisdn()[:9]}"})
        response = view(request)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "error" in response.data

    @patch("payments.views.verification_views.RazorpayService")
    def test_verify_invalid_signature(self, MockRazorpay, view, factory, fake_data):
        """Invalid payment signature should return 400."""
        mock_rp = MockRazorpay.return_value
        mock_rp.verify_payment_signature.return_value = False

        request = factory.post("/api/v1/payments/verify/", {
            "razorpay_order_id": f"order_{fake_data.msisdn()[:9]}",
            "razorpay_payment_id": f"pay_{fake_data.msisdn()[:9]}",
            "razorpay_signature": fake_data.sha256()
        })
        response = view(request)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["error"] == "Payment signature verification failed"

    @patch("payments.views.verification_views.TenantContext")
    @patch("payments.views.verification_views.transaction")
    @patch("payments.views.verification_views.Payment")
    @patch("payments.views.verification_views.RazorpayService")
    def test_verify_payment_not_found(
        self, MockRazorpay, MockPayment, mock_transaction, mock_ctx, view, factory, fake_data
    ):
        """Payment record not found should return 404."""
        mock_rp = MockRazorpay.return_value
        mock_rp.verify_payment_signature.return_value = True

        from payments.models import Payment as RealPayment
        MockPayment.DoesNotExist = RealPayment.DoesNotExist
        MockPayment.all_objects.select_related.return_value.get.side_effect = RealPayment.DoesNotExist

        request = factory.post("/api/v1/payments/verify/", {
            "razorpay_order_id": f"order_{fake_data.msisdn()[:9]}",
            "razorpay_payment_id": f"pay_{fake_data.msisdn()[:9]}",
            "razorpay_signature": fake_data.sha256()
        })
        response = view(request)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data["error"] == "Payment record not found"

    @patch("payments.views.verification_views.TenantContext")
    @patch("payments.views.verification_views.transaction")
    @patch("payments.views.verification_views.Payment")
    @patch("payments.views.verification_views.RazorpayService")
    def test_verify_success(
        self, MockRazorpay, MockPayment, mock_transaction, MockTenantCtx, view, factory, fake_data
    ):
        """Valid signature with found payment should activate subscription."""
        mock_rp = MockRazorpay.return_value
        mock_rp.verify_payment_signature.return_value = True

        mock_payment = MagicMock()
        mock_payment.status = PaymentStatus.CREATED
        mock_payment.subscription = MagicMock()
        mock_payment.tenant = MagicMock()
        MockPayment.all_objects.select_related.return_value.get.return_value = mock_payment

        mock_ctx_instance = MagicMock()
        MockTenantCtx.return_value = mock_ctx_instance
        mock_ctx_instance.__enter__ = MagicMock(return_value=mock_ctx_instance)
        mock_ctx_instance.__exit__ = MagicMock(return_value=False)

        mock_transaction.atomic.return_value.__enter__ = MagicMock()
        mock_transaction.atomic.return_value.__exit__ = MagicMock(return_value=False)

        request = factory.post("/api/v1/payments/verify/", {
            "razorpay_order_id": f"order_{fake_data.msisdn()[:9]}",
            "razorpay_payment_id": f"pay_{fake_data.msisdn()[:9]}",
            "razorpay_signature": fake_data.sha256()
        })
        response = view(request)
        assert response.status_code == status.HTTP_200_OK
        assert "message" in response.data
        mock_payment.subscription.activate.assert_called_once()
