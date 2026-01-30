"""
Model for Subscription - Tracks tenant premium status.
"""
from django.db import models, transaction
from django.utils import timezone
from common.models import BaseModel
from common.enums import SubscriptionStatus, PaymentStatus, SubscriptionPlan


class Subscription(BaseModel):
    """
    Subscription model - Lifecycle for lifetime access.
    Each tenant has exactly ONE subscription.
    """
    tenant = models.OneToOneField(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='subscription'
    )
    status = models.CharField(
        max_length=20,
        choices=SubscriptionStatus.choices,
        default=SubscriptionStatus.CREATED
    )
    activated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "subscriptions"

    def __str__(self):
        return f"{self.tenant.name} - {self.status}"

    @transaction.atomic
    def activate(self, payment):
        """
        Idempotent activation of subscription.
        Updates tenant plan and subscription status.
        """
        if self.status != SubscriptionStatus.ACTIVE:
            self.status = SubscriptionStatus.ACTIVE
            self.activated_at = timezone.now()
            self.save(update_fields=['status', 'activated_at', 'updated_at'])

            # Correctly upgrade tenant plan
            self.tenant.subscription_plan = SubscriptionPlan.PREMIUM
            self.tenant.save(update_fields=['subscription_plan', 'updated_at'])

        # Always finalize the payment status on successful activation call
        payment.status = PaymentStatus.ACTIVATED
        payment.save(update_fields=['status', 'updated_at'])
