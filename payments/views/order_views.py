import logging
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.exceptions import ValidationError

from payments.models import Payment, Subscription
from payments.serializers import PaymentOrderResponseSerializer
from payments.services.razorpay_service import RazorpayService
from payments.authentication import CsrfExemptSessionAuthentication
from tenants.authentication import TenantAwareJWTAuthentication
from common.enums import SubscriptionStatus, PaymentStatus
from common.permissions import IsTenantAdmin
from common.constants import CURRENCY

logger = logging.getLogger(__name__)


class CreateOrderView(APIView):
    """
    API to create a Razorpay order and initialize a Payment record.
    Restricted to Tenant Admins.

    """

    authentication_classes = [
        TenantAwareJWTAuthentication,
        CsrfExemptSessionAuthentication,
    ]
    permission_classes = [IsTenantAdmin]

    def post(self, request):
        tenant = request.user.tenant

        if not tenant:
            logger.error("User with no tenant attempted operation")
            raise ValidationError("User must belong to a tenant")

        try:
            subscription, created = Subscription.objects.get_or_create(tenant=tenant)
        except Exception as e:
            logger.exception(f"Failed to get/create subscription: {str(e)}")
            raise ValidationError("Failed to create subscription record")

        if subscription.status == SubscriptionStatus.ACTIVE:
            logger.warning("Tenant already has active subscription")
            raise ValidationError("Tenant already has an active lifetime subscription.")

        rp_service = RazorpayService()
        amount = settings.PREMIUM_PRICE_PAISE
        currency = CURRENCY

        try:
            rp_order = rp_service.create_order(amount=amount, currency=currency)
            logger.info("Razorpay order created for tenant")
        except Exception as e:
            logger.exception(f"Failed to create Razorpay order: {str(e)}")
            raise ValidationError("Failed to create payment order. Please try again.")

        try:
            payment = Payment.objects.create(
                tenant=tenant,
                subscription=subscription,
                initiated_by=request.user,
                razorpay_order_id=rp_order["id"],
                amount=amount,
                currency=currency,
                status=PaymentStatus.CREATED,
            )
            logger.info("Payment record created successfully")
        except Exception as e:
            logger.exception(f"Failed to create Payment record: {str(e)}")
            raise ValidationError("Failed to save payment record. Please try again.")

        serializer = PaymentOrderResponseSerializer(
            {
                "razorpay_order_id": payment.razorpay_order_id,
                "amount": payment.amount,
                "currency": payment.currency,
                "status": payment.status,
            }
        )

        return Response(serializer.data, status=status.HTTP_201_CREATED)
