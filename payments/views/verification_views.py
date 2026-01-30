import logging
from django.db import transaction
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.permissions import AllowAny

from payments.models import Payment
from payments.services.razorpay_service import RazorpayService
from common.enums import PaymentStatus
from tenants.context import TenantContext

logger = logging.getLogger(__name__)


class VerifyPaymentView(APIView):
    """
    Verify payment signature and activate subscription.

    """

    permission_classes = [AllowAny]

    def post(self, request):
        razorpay_order_id = request.data.get("razorpay_order_id")
        razorpay_payment_id = request.data.get("razorpay_payment_id")
        razorpay_signature = request.data.get("razorpay_signature")

        if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature]):
            return Response(
                {
                    "error": "Missing required fields: razorpay_order_id, razorpay_payment_id, razorpay_signature"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        rp_service = RazorpayService()
        if not rp_service.verify_payment_signature(
            razorpay_order_id, razorpay_payment_id, razorpay_signature
        ):
            logger.warning("Payment verification failed: Signature mismatch")
            return Response(
                {"error": "Payment signature verification failed"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        logger.info("Payment signature verified successfully")

        try:
            payment = Payment.all_objects.select_related("tenant", "subscription").get(
                razorpay_order_id=razorpay_order_id
            )
            logger.info("Payment found, processing verification")
        except Payment.DoesNotExist:
            logger.error("Payment not found in database")
            return Response(
                {"error": "Payment record not found"}, status=status.HTTP_404_NOT_FOUND
            )

        with TenantContext(payment.tenant):
            # Always save signature and payment ID if the verification succeeded
            payment.razorpay_payment_id = razorpay_payment_id
            payment.razorpay_signature = razorpay_signature

            # If already processed, just save the signature and return
            if payment.status in [PaymentStatus.VERIFIED, PaymentStatus.ACTIVATED]:
                payment.save(update_fields=["razorpay_payment_id", "razorpay_signature", "updated_at"])
                logger.info("Payment already verified. Updated signature metadata.")
                return Response(
                    {
                        "message": "Payment already verified and subscription activated",
                        "order_id": razorpay_order_id,
                        "status": payment.status,
                        "subscription_status": payment.subscription.status,
                    },
                    status=status.HTTP_200_OK,
                )

            # Otherwise, perform the full activation in a transaction
            with transaction.atomic():
                payment.status = PaymentStatus.VERIFIED
                payment.verified_at = timezone.now()
                payment.save(
                    update_fields=[
                        "razorpay_payment_id",
                        "razorpay_signature",
                        "status",
                        "verified_at",
                        "updated_at",
                    ]
                )

                payment.subscription.activate(payment)
                logger.info("Payment verified and subscription activated")

        return Response(
            {
                "message": "Payment verified and subscription activated successfully!",
                "order_id": razorpay_order_id,
                "payment_id": razorpay_payment_id,
                "status": payment.status,
                "subscription_status": payment.subscription.status,
            },
            status=status.HTTP_200_OK,
        )
