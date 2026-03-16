import pytest
from payments.models.payment import Payment
from common.enums import PaymentStatus


@pytest.mark.django_db
class TestPaymentModelUnit:
    """Unit tests for Payment model."""

    def test_payment_str(self, payment_factory, fake_data):
        """Test the string representation of the payment."""
        order_id = f"order_{fake_data.msisdn()[:9]}"
        payment = payment_factory.build(
            razorpay_order_id=order_id, status=PaymentStatus.CREATED
        )
        assert str(payment) == f"{order_id} - CREATED"
