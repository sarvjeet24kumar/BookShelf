"""
Checkout view - Renders Razorpay checkout page.
"""
import logging
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer

from payments.models import Subscription
from payments.authentication import CsrfExemptSessionAuthentication, JWTQueryParamAuthentication
from tenants.authentication import TenantAwareJWTAuthentication
from common.enums import SubscriptionStatus
from common.permissions import IsTenantAdmin

logger = logging.getLogger(__name__)


class CheckoutView(APIView):
    """
    Renders the Razorpay checkout page.
    Automatically creates or retrieves a pending order.

    """
    authentication_classes = [TenantAwareJWTAuthentication, JWTQueryParamAuthentication, CsrfExemptSessionAuthentication]
    permission_classes = [permissions.IsAuthenticated, IsTenantAdmin]
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]

    def get(self, request):
        user = request.user
        logger.info(f"Checkout access attempt: user={user.username}, role={user.role}, tenant={user.tenant}")
        tenant = user.tenant
    
        if not tenant:
            return Response(
                {"detail": "Payments are restricted to Tenant Admins."},
                status=status.HTTP_403_FORBIDDEN
            )

        subscription, _ = Subscription.objects.get_or_create(tenant=tenant)

        if subscription.status == SubscriptionStatus.ACTIVE:
            return Response(
                {
                    "detail": "You already have an active subscription.",
                    "subscription_status": subscription.status,
                    "activated_at": subscription.activated_at,
                },
                template_name="payments/already_active.html",
                status=status.HTTP_200_OK
            )

        return Response(
            {
                "RAZORPAY_KEY_ID": settings.RAZORPAY_KEY_ID
            },
            template_name="payments/checkout.html"
        )
