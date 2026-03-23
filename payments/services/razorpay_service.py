import razorpay
import logging
from django.conf import settings
from rest_framework.exceptions import ValidationError

logger = logging.getLogger(__name__)


class RazorpayService:
    def __init__(self):
        try:
            self.client = razorpay.Client(
                auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
            )
        except Exception as e:
            logger.error(f"Razorpay client initialization failed: {str(e)}")
            self.client = None

    def create_order(self, amount, currency="INR"):
        if not self.client:
            raise ValidationError("Payment service is currently unavailable.")

        data = {"amount": amount, "currency": currency, "payment_capture": 1}
        try:
            order = self.client.order.create(data=data)
            logger.info("Razorpay order created successfully")
            return order
        except Exception as e:
            logger.error(f"Razorpay order creation failed: {str(e)}")
            raise ValidationError(f"Failed to create payment order: {str(e)}")

    def verify_payment_signature(
        self, razorpay_order_id, razorpay_payment_id, razorpay_signature
    ):
        """
        Verify payment signature for client-side verification.
        This is used when payment completes and we want to verify without waiting for webhook.

        """
        if not self.client:
            return False

        try:
            params = {
                "razorpay_order_id": razorpay_order_id,
                "razorpay_payment_id": razorpay_payment_id,
                "razorpay_signature": razorpay_signature,
            }
            self.client.utility.verify_payment_signature(params)
            logger.info("Payment signature verified")
            return True
        except razorpay.errors.SignatureVerificationError:
            logger.warning("Payment signature verification failed")
            return False
        except Exception as e:
            logger.error(f"Error verifying payment signature: {str(e)}")
            return False

    def fetch_payment_status(self, razorpay_order_id):
        """
        Fetch order status and payments directly from Razorpay API.
        Useful for manual verification when webhooks fail.

        """
        if not self.client:
            return None

        try:
            order = self.client.order.fetch(razorpay_order_id)
            result = {
                "order_status": order.get("status"),
                "amount_paid": order.get("amount_paid", 0),
                "payment_id": None,
                "captured": False,
            }

            if order.get("status") == "paid":
                payments = self.client.order.payments(razorpay_order_id)
                for payment in payments.get("items", []):
                    if payment.get("status") == "captured":
                        result["payment_id"] = payment.get("id")
                        result["captured"] = True
                        break

            return result
        except Exception as e:
            logger.error(f"Error fetching payment status: {str(e)}")
            return None

    def verify_webhook_signature(self, payload, signature):
        if not self.client:
            return False

        try:
            self.client.utility.verify_webhook_signature(
                payload, signature, settings.RAZORPAY_WEBHOOK_SECRET
            )
            return True
        except razorpay.errors.SignatureVerificationError:
            logger.warning("Razorpay webhook signature verification failed.")
            return False
        except Exception as e:
            logger.error(f"Error verifying Razorpay signature: {str(e)}")
            return False
