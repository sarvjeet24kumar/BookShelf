import logging
import json
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

from payments.models import WebhookEvent
from payments.services.razorpay_service import RazorpayService
from payments.tasks import process_webhook_task

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class RazorpayWebhookView(APIView):
    """
    Public webhook endpoint for Razorpay events.
    Handles payment.captured and payment.failed.

    """
    permission_classes = [permissions.AllowAny]

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
        
        if not event_id:
            payment_data = data.get("payload", {}).get("payment", {}).get("entity", {})
            payment_id = payment_data.get("id")
            if payment_id:
                event_id = f"evt_manual_{payment_id}"
            else:
                event_id = f"evt_unknown_{timezone.now().timestamp()}"
                logger.warning(f"Webhook missing 'id' field, using generated ID: {event_id}")
        
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
                    "event_type": event_type or "unknown",
                    "payload": audit_payload,
                    "processed": False,
                    "error_message": None
                }
            )
            
            if not created:
                if webhook_event.processed:
                    logger.info(f"Webhook {event_id} already processed. Skipping.")
                    return Response({"status": "already_processed"}, status=status.HTTP_200_OK)
                else:
                    logger.info(f"Webhook {event_id} exists but unprocessed. Retrying")
            else:
                logger.info(f"Webhook {event_id} persisted (Phase 1)")
                
        except Exception as e:
            logger.exception(f"CRITICAL: Failed to persist webhook {event_id}: {str(e)}")
            return Response({"error": "Failed to save webhook"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        if not event_type:
            error_msg = "Missing event_type in payload"
            logger.error(f"{error_msg} for webhook {event_id}")
            webhook_event.error_message = error_msg
            webhook_event.save(update_fields=['error_message', 'updated_at'])
            return Response({"error": "Malformed payload - missing event type"}, status=status.HTTP_400_BAD_REQUEST)
        
        rp_service = RazorpayService()
        if not rp_service.verify_webhook_signature(payload_str, signature):
            error_msg = "Signature verification failed"
            logger.error(f"{error_msg} for webhook {event_id}")
            webhook_event.error_message = error_msg
            webhook_event.save(update_fields=['error_message', 'updated_at'])
            return Response({"error": "Invalid signature"}, status=status.HTTP_400_BAD_REQUEST)
        
        logger.info(f"Webhook {event_id} signature verified (Phase 2)")
        
        try:
            process_webhook_task.delay(event_id)
            logger.info(f"Webhook {event_id} ({event_type}) offloaded to Celery task.")
        except Exception as e:
            error_msg = f"Failed to initiate Celery task: {str(e)}"
            logger.exception(f"{error_msg}")
            webhook_event.error_message = error_msg
            webhook_event.save(update_fields=['error_message', 'updated_at'])
            return Response({"error": "Failed to initiate processing"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({"status": "received", "event_id": event_id}, status=status.HTTP_202_ACCEPTED)
