import logging
from celery import shared_task
from django.db import transaction
from django.utils import timezone
from .models import Payment, Subscription, WebhookEvent
from .services.razorpay_service import RazorpayService
from common.enums import PaymentStatus, RazorpayOrderStatus, RazorpayPaymentStatus
from tenants.context import TenantContext
from common.constants import CELERY_MAX_RETRIES, CELERY_COUNTDOWN_LONG

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=CELERY_MAX_RETRIES)
def process_webhook_task(self, event_id):
    """
    Asynchronously processes a Razorpay webhook event.

    """
    try:
        webhook_event = WebhookEvent.objects.get(event_id=event_id, processed=False)
    except WebhookEvent.DoesNotExist:
        logger.warning("Webhook already processed or not found.")
        return "Webhook already processed or not found."

    payload = webhook_event.payload
    event_type = webhook_event.event_type
    data = payload.get("payload", {})
    payment_data = data.get("payment", {}).get("entity", {})
    order_id = payment_data.get("order_id")
    payment_id = payment_data.get("id")

    if not order_id:
        error_msg = "Webhook missing order_id in payload."
        logger.error(error_msg)
        webhook_event.error_message = error_msg
        webhook_event.processed = True
        webhook_event.save(update_fields=["error_message", "processed", "updated_at"])
        return error_msg

    try:
        payment = Payment.all_objects.select_related("tenant", "subscription").get(
            razorpay_order_id=order_id
        )
        tenant = payment.tenant
        with TenantContext(tenant):
            with transaction.atomic():
                if event_type == "payment.captured":
                    _handle_captured(order_id, payment_id)
                elif event_type == "payment.failed":
                    _handle_failed(order_id)
                else:
                    logger.warning("Unhandled webhook event type")

                webhook_event.processed = True
                webhook_event.save(update_fields=["processed", "updated_at"])
                logger.info("Successfully processed webhook event")
                return "Successfully processed webhook event"

    except Payment.DoesNotExist:
        error_msg = "Payment not found for order reference"
        logger.error(error_msg)
        webhook_event.error_message = error_msg
        webhook_event.processed = True
        webhook_event.save(update_fields=["error_message", "processed", "updated_at"])
        return error_msg
    except Exception as e:
        logger.exception(f"Error processing webhook task: {str(e)}")
        webhook_event.error_message = str(e)
        webhook_event.save(update_fields=["error_message", "updated_at"])
        raise self.retry(exc=e, countdown=CELERY_COUNTDOWN_LONG)


def _handle_captured(order_id, payment_id):
    """
    Internal helper for captured logic with idempotency checks.
    """
    payment = Payment.objects.select_for_update().get(razorpay_order_id=order_id)

    if payment.status in [PaymentStatus.VERIFIED, PaymentStatus.ACTIVATED]:
        logger.info("Payment already verified. Skipping webhook processing.")
        return

    payment.razorpay_payment_id = payment_id
    payment.status = PaymentStatus.VERIFIED
    payment.verified_at = timezone.now()
    payment.save(
        update_fields=["razorpay_payment_id", "status", "verified_at", "updated_at"]
    )

    payment.subscription.activate(payment)
    logger.info("Payment captured and subscription activated via webhook.")


def _handle_failed(order_id):
    """
    Internal helper for failed logic.
    """
    try:
        payment = Payment.objects.get(razorpay_order_id=order_id)
        if payment.status == PaymentStatus.CREATED:
            payment.status = PaymentStatus.FAILED
            payment.save(update_fields=["status", "updated_at"])
            logger.info("Payment marked as failed.")
    except Payment.DoesNotExist:
        logger.warning("Payment record not found")


@shared_task
def reconcile_payments_task():
    """
    Periodic job to reconcile payments stuck in CREATED state.
    Checks Razorpay API for status updates.
    """
    stuck_payments = Payment.all_objects.select_related(
        "tenant", "subscription"
    ).filter(
        status__in=[PaymentStatus.CREATED, PaymentStatus.PAID],
        created_at__lt=timezone.now() - timezone.timedelta(minutes=5),
    )

    rp_service = RazorpayService()
    reconciled_count = 0

    for payment in stuck_payments:
        try:
            with TenantContext(payment.tenant):
                order_data = rp_service.client.order.fetch(payment.razorpay_order_id)
                rp_status = order_data.get("status")

                if rp_status == RazorpayOrderStatus.PAID:
                    with transaction.atomic():
                        payment.status = PaymentStatus.PAID
                        payment.save(update_fields=["status", "updated_at"])
                        rp_payments = rp_service.client.order.payments(
                            payment.razorpay_order_id
                        )
                        for rp_payment in rp_payments.get("items", []):
                            if rp_payment.get("status") == RazorpayPaymentStatus.CAPTURED:
                                _handle_captured(
                                    payment.razorpay_order_id, rp_payment.get("id")
                                )
                                reconciled_count += 1
                                break

                elif (
                    rp_status == RazorpayOrderStatus.ATTEMPTED
                    and payment.created_at
                    < timezone.now() - timezone.timedelta(hours=24)
                ):
                    payment.status = PaymentStatus.FAILED
                    payment.save(update_fields=["status", "updated_at"])

        except Exception as e:
            logger.error(
                f"Failed to reconcile payment: {str(e)}"
            )

    logger.info(f"Reconciliation complete. {reconciled_count} payments reconciled.")
    return f"Reconciled {reconciled_count} payments."
