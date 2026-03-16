import pytest
from payments.models.webhook_event import WebhookEvent


@pytest.mark.django_db
class TestWebhookEventModelUnit:
    """Unit tests for WebhookEvent model."""

    def test_webhook_event_str(self, fake_data):
        """Test the string representation of the WebhookEvent."""
        event_id = f"evt_{fake_data.msisdn()[:9]}"
        event_type = "payment.captured"
        event = WebhookEvent(event_id=event_id, event_type=event_type)
        assert str(event) == f"{event_id} - {event_type}"
