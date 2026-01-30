import logging
import json
from datetime import datetime
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from payments.models import WebhookEvent, Payment
from payments.services.razorpay_service import RazorpayService
from payments.tasks import process_webhook_task
from tenants.context import set_current_tenant

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class RazorpayWebhookView(APIView):
    """
    Public webhook endpoint for Razorpay events.
    Handles payment.captured and payment.failed.

    """
    permission_classes = [AllowAny]

    def post(self, request):
        
        signature = request.headers.get("X-Razorpay-Signature", "")
        
        try:
            payload_bytes = request.body
            payload_str = payload_bytes.decode("utf-8")
        except Exception as e:
            logger.error(f"Failed to decode webhook payload: {str(e)}")
            return Response({"error": "Invalid payload encoding"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            data = json.loads(payload_str)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse webhook JSON: {str(e)}")
            return Response({"error": "Invalid JSON"}, status=status.HTTP_400_BAD_REQUEST)
        
        event_type = data.get("event", "")
        event_id = data.get("id")
        
        if event_type not in ["payment.captured", "payment.failed"]:
            logger.info("Ignoring unsupported webhook event type")
            return Response({"status": "ignored", "event_type": event_type}, status=status.HTTP_200_OK)
        
        payment_data = data.get("payload", {}).get("payment", {}).get("entity", {})
        payment_id = payment_data.get("id")
        order_id = payment_data.get("order_id")
        
        if not payment_id:
            logger.error("Webhook missing payment reference")
            return Response({"error": "Missing payment_id"}, status=status.HTTP_400_BAD_REQUEST)
        
        if not order_id:
            logger.error("Webhook missing order reference")
            return Response({"error": "Missing order_id"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Identify tenant for logging context
        try:
            payment = Payment.all_objects.select_related('tenant').get(razorpay_order_id=order_id)
            set_current_tenant(payment.tenant)
        except Payment.DoesNotExist:
            logger.warning(f"Tenant identification failed: Payment not found for order {order_id}")

        if not event_id:
            event_id = f"evt_manual_{payment_id}"
            logger.warning("Webhook missing 'id' field, using generated ID")
        
        # Convert Razorpay's unix timestamp to readable format for auditing within the payload
        razorpay_created_at = data.get("created_at")
        if isinstance(razorpay_created_at, int):
            data["created_at"] = datetime.fromtimestamp(razorpay_created_at, tz=timezone.UTC).isoformat()

        audit_payload = {
            **data,
            "_webhook_metadata": {
                "signature": signature[:50] + "..." if len(signature) > 50 else signature,
                "received_at": timezone.now().isoformat(),
                "has_signature": bool(signature)
            }
        }
        
        webhook_event = None
        try:

            webhook_event, created = WebhookEvent.objects.get_or_create(
                event_id=event_id,
                defaults={
                    "event_type": event_type,
                    "payload": audit_payload,
                    "processed": False,
                    "error_message": None
                }
            )
            
            if not created:
                if webhook_event.processed:
                    logger.info("Webhook already processed. Skipping.")
                    return Response({"status": "already_processed"}, status=status.HTTP_200_OK)
                else:
                    logger.info("Webhook exists but unprocessed. Retrying")
            else:
                logger.info("Webhook persisted (Phase 1)")
                
        except Exception as e:
            logger.exception(f"CRITICAL: Failed to persist webhook: {str(e)}")
            return Response({"error": "Failed to save webhook"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        if not event_type:
            error_msg = "Missing event_type in payload"
            logger.error(error_msg)
            webhook_event.error_message = error_msg
            webhook_event.save(update_fields=['error_message', 'updated_at'])
            return Response({"error": "Malformed payload - missing event type"}, status=status.HTTP_400_BAD_REQUEST)
        
        rp_service = RazorpayService()
        if not rp_service.verify_webhook_signature(payload_str, signature):
            error_msg = "Signature verification failed"
            logger.error(error_msg)
            webhook_event.error_message = error_msg
            webhook_event.save(update_fields=['error_message', 'updated_at'])
            return Response({"error": "Invalid signature"}, status=status.HTTP_400_BAD_REQUEST)
        
        logger.info("Webhook signature verified (Phase 2)")
        
        try:
            process_webhook_task.delay(event_id)
            logger.info("Webhook offloaded to Celery task.")
        except Exception as e:
            error_msg = f"Failed to initiate Celery task: {str(e)}"
            logger.exception(f"{error_msg}")
            webhook_event.error_message = error_msg
            webhook_event.save(update_fields=['error_message', 'updated_at'])
            return Response({"error": "Failed to initiate processing"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({"status": "received", "event_id": event_id}, status=status.HTTP_202_ACCEPTED)
