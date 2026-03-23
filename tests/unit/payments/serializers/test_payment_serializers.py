import pytest
from payments.serializers import (
    PaymentOrderResponseSerializer,
    WebhookEventSerializer,
    SubscriptionAdminSerializer,
    PaymentAdminSerializer,
)


class TestPaymentSerializersUnit:
    """Unit tests for payment serializers."""

    def test_payment_order_response_serializer(self, fake_data):
        """Test simple field serialization of PaymentOrderResponseSerializer."""
        order_id = f"order_{fake_data.msisdn()[:9]}"
        data = {
            "razorpay_order_id": order_id,
            "amount": 999,
            "currency": "INR",
            "status": "created",
        }
        serializer = PaymentOrderResponseSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data["razorpay_order_id"] == order_id

    def test_webhook_event_serializer(self, fake_data):
        """Test JSON field in WebhookEventSerializer."""
        event_id = f"evt_{fake_data.msisdn()[:9]}"
        order_id = f"order_{fake_data.msisdn()[:9]}"
        data = {
            "id": event_id,
            "event": "order.paid",
            "payload": {"order_id": order_id},
        }
        serializer = WebhookEventSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data["payload"]["order_id"] == order_id


@pytest.mark.django_db
class TestPaymentAdminSerializersUnit:
    """Unit tests for Payment Admin serializers."""

    def test_subscription_admin_serializer_read_only(self, subscription):
        """Test read-only fields and source fields in SubscriptionAdminSerializer."""
        serializer = SubscriptionAdminSerializer(instance=subscription)
        data = serializer.data
        assert "tenant_name" in data
        assert "tenant_slug" in data
        assert data["tenant_name"] == subscription.tenant.name

    def test_payment_admin_serializer_read_only(self, payment):
        """Test read-only fields and source fields in PaymentAdminSerializer."""
        serializer = PaymentAdminSerializer(instance=payment)
        data = serializer.data
        assert "tenant_name" in data
        assert "initiated_by_username" in data
        assert data["initiated_by_username"] == payment.initiated_by.username
