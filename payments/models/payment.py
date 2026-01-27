"""
Model for Payment - Tracks Razorpay payment attempts.
"""
from django.db import models
from common.models import TenantAwareModel
from common.enums import PaymentStatus
from django.contrib.auth import get_user_model

User = get_user_model()


class Payment(TenantAwareModel):
    """
    Payment model - Tracks individual Razorpay order attempts.
    """
    subscription = models.ForeignKey(
        'payments.Subscription',
        on_delete=models.CASCADE,
        related_name='payments'
    )
    initiated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='initiated_payments'
    )
    razorpay_order_id = models.CharField(max_length=100, unique=True)
    razorpay_payment_id = models.CharField(max_length=100, null=True, blank=True)
    razorpay_signature = models.CharField(max_length=255, null=True, blank=True)
    amount = models.PositiveIntegerField()
    currency = models.CharField(max_length=10, default='INR')
    status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.CREATED
    )
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "payments"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.razorpay_order_id} - {self.status}"
