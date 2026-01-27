from rest_framework import serializers
from .models import Payment, Subscription, WebhookEvent

class PaymentOrderResponseSerializer(serializers.Serializer):
    razorpay_order_id = serializers.CharField()
    amount = serializers.IntegerField()
    currency = serializers.CharField()
    status = serializers.CharField()


class WebhookEventSerializer(serializers.Serializer):
    id = serializers.CharField()
    event = serializers.CharField()
    payload = serializers.JSONField()


class SubscriptionAdminSerializer(serializers.ModelSerializer):
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    tenant_slug = serializers.CharField(source='tenant.slug', read_only=True)

    class Meta:
        model = Subscription
        fields = [
            'id', 'tenant', 'tenant_name', 'tenant_slug',
            'status', 'activated_at', 'created_at', 'updated_at',
        ]
        read_only_fields = fields


class PaymentAdminSerializer(serializers.ModelSerializer):
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    initiated_by_username = serializers.CharField(source='initiated_by.username', read_only=True)

    class Meta:
        model = Payment
        fields = [
            'id', 'tenant', 'tenant_name', 'subscription',
            'initiated_by', 'initiated_by_username',
            'razorpay_order_id', 'razorpay_payment_id',
            'amount', 'currency', 'status',
            'verified_at', 'created_at', 'updated_at',
        ]
        read_only_fields = fields


class WebhookEventAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = WebhookEvent
        fields = [
            'id', 'event_id', 'event_type', 'payload',
            'processed', 'error_message', 'created_at', 'updated_at',
        ]
        read_only_fields = fields
