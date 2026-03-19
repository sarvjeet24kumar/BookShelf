"""Unit tests for RazorpayWebhookView ."""

import pytest
import json
from unittest.mock import patch, MagicMock
from rest_framework import status
from rest_framework.test import APIRequestFactory
from payments.models import Payment as RealPayment
from payments.views.webhook_views import RazorpayWebhookView


@pytest.fixture
def view():
    return RazorpayWebhookView.as_view()


@pytest.fixture
def factory():
    return APIRequestFactory()


def _make_webhook_payload(
    fake_data,
    event_type="payment.captured",
    payment_id=None,
    order_id=None,
    event_id=None,
):
    payment_id = payment_id or f"pay_{fake_data.msisdn()[:9]}"
    order_id = order_id or f"order_{fake_data.msisdn()[:9]}"
    event_id = event_id or f"evt_{fake_data.msisdn()[:9]}"
    return {
        "event": event_type,
        "id": event_id,
        "payload": {"payment": {"entity": {"id": payment_id, "order_id": order_id}}},
    }


class TestRazorpayWebhookView:
    """Unit tests for RazorpayWebhookView.post()."""

    def test_webhook_invalid_json(self, view, factory):
        """Non-JSON body should return 400."""
        request = factory.post(
            "/api/v1/payments/webhook/", data="not json", content_type="text/plain"
        )
        response = view(request)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_webhook_unsupported_event_type(self, view, factory, fake_data):
        """Unsupported event type should be ignored with 200."""
        payload = _make_webhook_payload(
            fake_data,
            event_type="order.created",
            payment_id=f"pay_{fake_data.msisdn()[:9]}",
            order_id=f"order_{fake_data.msisdn()[:9]}",
            event_id=f"evt_{fake_data.msisdn()[:9]}",
        )

        request = factory.post(
            "/api/v1/payments/webhook/",
            data=json.dumps(payload),
            content_type="application/json",
        )
        response = view(request)
        assert response.status_code == status.HTTP_200_OK
        assert response.data.get("status") == "ignored"

    def test_webhook_missing_payment_id(self, view, factory, fake_data):
        """Webhook with no payment_id should return 400."""
        payload = {
            "event": "payment.captured",
            "id": f"evt_{fake_data.msisdn()[:9]}",
            "payload": {"payment": {"entity": {}}},
        }

        request = factory.post(
            "/api/v1/payments/webhook/",
            data=json.dumps(payload),
            content_type="application/json",
        )
        response = view(request)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["error"] == "Missing payment_id"


    @patch("payments.views.webhook_views.RazorpayService")
    @patch("payments.views.webhook_views.WebhookEvent")
    @patch("payments.views.webhook_views.Payment")
    def test_webhook_invalid_signature(
        self, MockPayment, MockWebhookEvent, MockRazorpay, view, factory, fake_data
    ):
        """Invalid signature should return 400."""
        payload = _make_webhook_payload(
            fake_data,
            payment_id=f"pay_{fake_data.msisdn()[:9]}",
            order_id=f"order_{fake_data.msisdn()[:9]}",
            event_id=f"evt_{fake_data.msisdn()[:9]}",
        )

        mock_payment = MagicMock()
        mock_payment.tenant = MagicMock()
        MockPayment.all_objects.select_related.return_value.get.return_value = (
            mock_payment
        )

        mock_event = MagicMock()
        MockWebhookEvent.objects.get_or_create.return_value = (mock_event, True)

        mock_rp = MockRazorpay.return_value
        mock_rp.verify_webhook_signature.return_value = False

        request = factory.post(
            "/api/v1/payments/webhook/",
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_X_RAZORPAY_SIGNATURE=fake_data.sha256(),
        )
        response = view(request)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["error"] == "Invalid signature"

    @patch("payments.views.webhook_views.WebhookEvent")
    @patch("payments.views.webhook_views.Payment")
    def test_webhook_already_processed(
        self, MockPayment, MockWebhookEvent, view, factory, fake_data
    ):
        """Already processed event should return 200 with already_processed."""
        payload = _make_webhook_payload(
            fake_data,
            payment_id=f"pay_{fake_data.msisdn()[:9]}",
            order_id=f"order_{fake_data.msisdn()[:9]}",
            event_id=f"evt_{fake_data.msisdn()[:9]}",
        )

        mock_payment = MagicMock()
        mock_payment.tenant = MagicMock()
        MockPayment.all_objects.select_related.return_value.get.return_value = (
            mock_payment
        )

        mock_event = MagicMock()
        mock_event.processed = True
        MockWebhookEvent.objects.get_or_create.return_value = (mock_event, False)

        request = factory.post(
            "/api/v1/payments/webhook/",
            data=json.dumps(payload),
            content_type="application/json",
        )
        response = view(request)
        assert response.status_code == status.HTTP_200_OK
        assert response.data.get("status") == "already_processed"

    def test_webhook_missing_order_id(self, view, factory, fake_data):
        """Webhook with no order_id should return 400."""
        payload = _make_webhook_payload(fake_data, event_type="payment.captured", payment_id=f"pay_{fake_data.msisdn()[:9]}", event_id=f"evt_{fake_data.msisdn()[:9]}")
        payload["payload"]["payment"]["entity"]["order_id"] = None

        request = factory.post(
            "/api/v1/payments/webhook/",
            data=json.dumps(payload),
            content_type="application/json",
        )
        response = view(request)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["error"] == "Missing order_id"

   