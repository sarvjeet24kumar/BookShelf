import pytest
from payments.models.subscription import Subscription
from common.enums import SubscriptionStatus, PaymentStatus, SubscriptionPlan
from django.utils import timezone

@pytest.mark.django_db
class TestSubscriptionModelUnit:
    """Unit tests for Subscription model and its methods."""

    def test_subscription_str(self, subscription_factory):
        """Test the string representation of the subscription."""
        subscription = subscription_factory.create(status=SubscriptionStatus.ACTIVE)
        expected_str = f"{subscription.tenant.name} - {SubscriptionStatus.ACTIVE}"
        assert str(subscription) == expected_str

    def test_subscription_activate_logic(self, subscription, payment):
        """Test the activate method updates subscription, tenant and payment."""
        # Initial state
        subscription.status = SubscriptionStatus.CREATED
        subscription.save()
        tenant = subscription.tenant
        tenant.subscription_plan = SubscriptionPlan.FREE
        tenant.save()
        payment.status = PaymentStatus.VERIFIED
        payment.save()

        # Execute activation
        subscription.activate(payment)

        # Re-fetch and assert
        subscription.refresh_from_db()
        tenant.refresh_from_db()
        payment.refresh_from_db()

        assert subscription.status == SubscriptionStatus.ACTIVE
        assert subscription.activated_at is not None
        assert tenant.subscription_plan == SubscriptionPlan.PREMIUM
        assert payment.status == PaymentStatus.ACTIVATED

    def test_subscription_activate_idempotency(self, subscription, payment):
        """Test that calling activate twice doesn't change activated_at."""
        subscription.status = SubscriptionStatus.ACTIVE
        subscription.activated_at = timezone.now() - timezone.timedelta(days=1)
        original_activated_at = subscription.activated_at
        subscription.save()

        subscription.activate(payment)
        subscription.refresh_from_db()

        assert subscription.status == SubscriptionStatus.ACTIVE
        assert subscription.activated_at == original_activated_at
