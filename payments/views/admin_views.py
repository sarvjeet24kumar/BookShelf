import logging
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.exceptions import NotFound

from payments.models import Subscription, Payment, WebhookEvent
from payments.serializers import (
    SubscriptionAdminSerializer,
    PaymentAdminSerializer,
    WebhookEventAdminSerializer,
)
from common.permissions import IsSuperAdmin
from common.pagination import CommonPagination
from common.enums import UserRole

logger = logging.getLogger(__name__)


class SubscriptionListView(ListAPIView):
    """
    List all subscriptions.
    SuperAdmin only.
    """

    permission_classes = [IsSuperAdmin]
    serializer_class = SubscriptionAdminSerializer
    pagination_class = CommonPagination
    queryset = Subscription.objects.select_related("tenant").all()


class SubscriptionDetailView(RetrieveAPIView):
    """
    Retrieve subscription details.
    SuperAdmin only.
    """

    permission_classes = [IsSuperAdmin]
    serializer_class = SubscriptionAdminSerializer
    lookup_field = "id"
    queryset = Subscription.objects.select_related("tenant").all()


class PaymentListView(ListAPIView):
    """
    List all payments.
    SuperAdmin only.
    """

    permission_classes = [IsSuperAdmin]
    serializer_class = PaymentAdminSerializer
    pagination_class = CommonPagination
    queryset = Payment.all_objects.select_related(
        "tenant", "subscription", "initiated_by"
    ).all()


class PaymentDetailView(RetrieveAPIView):
    """
    Retrieve payment details.
    SuperAdmin only.
    """

    permission_classes = [IsSuperAdmin]
    serializer_class = PaymentAdminSerializer
    lookup_field = "id"
    queryset = Payment.all_objects.select_related(
        "tenant", "subscription", "initiated_by"
    ).all()


class WebhookEventListView(ListAPIView):
    """
    List webhook events.
    SuperAdmin only
    """

    permission_classes = [IsSuperAdmin]
    serializer_class = WebhookEventAdminSerializer
    pagination_class = CommonPagination
    queryset = WebhookEvent.objects.all()


class WebhookEventDetailView(RetrieveAPIView):
    """
    Retrieve webhook event details.
    - SuperAdmin only
    """

    permission_classes = [IsSuperAdmin]
    serializer_class = WebhookEventAdminSerializer
    lookup_field = "id"
    queryset = WebhookEvent.objects.all()
