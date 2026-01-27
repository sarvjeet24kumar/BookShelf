"""
Model for WebhookEvent - Logs Razorpay webhooks for auditing.
"""
from django.db import models
from common.models import BaseModel


class WebhookEvent(BaseModel):
    """
    Logs raw Razorpay webhooks for auditing and idempotency.
    """
    event_id = models.CharField(max_length=100, unique=True)
    event_type = models.CharField(max_length=100)
    payload = models.JSONField()
    processed = models.BooleanField(default=False)
    error_message = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "webhook_events"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.event_id} - {self.event_type}"
