from django.urls import path
from .views import (
    CreateOrderView,
    RazorpayWebhookView,
    CheckoutView,
    VerifyPaymentView,
    SubscriptionListView,
    SubscriptionDetailView,
    PaymentListView,
    PaymentDetailView,
    WebhookEventListView,
    WebhookEventDetailView,
)

urlpatterns = [
    path("create-order/", CreateOrderView.as_view(), name="create-order"),
    path("checkout/", CheckoutView.as_view(), name="checkout"),
    path("verify/", VerifyPaymentView.as_view(), name="verify-payment"),
    path("webhook/razorpay/", RazorpayWebhookView.as_view(), name="razorpay-webhook"),
    

    path("subscriptions/", SubscriptionListView.as_view(), name="subscription-list"),
    path("subscriptions/<uuid:id>/", SubscriptionDetailView.as_view(), name="subscription-detail"),
    path("payment-history/", PaymentListView.as_view(), name="payment-list"),
    path("payment-history/<uuid:id>/", PaymentDetailView.as_view(), name="payment-detail"),
    path("webhooks/", WebhookEventListView.as_view(), name="webhook-list"),
    path("webhooks/<uuid:id>/", WebhookEventDetailView.as_view(), name="webhook-detail"),
]
