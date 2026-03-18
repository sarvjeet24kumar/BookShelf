import pytest
import uuid
from django.urls import reverse
from rest_framework import status
from unittest.mock import patch

@pytest.mark.django_db
class TestPaymentViews:
    """Integration tests for Payments."""

    @patch("payments.views.order_views.RazorpayService")
    def test_create_order(self, mock_rp_class, api_client, admin_user, tenant, faker):
        api_client.force_authenticate(user=admin_user)
        url = reverse("create-order")
        
        mock_rp = mock_rp_class.return_value
        order_id = f"order_{uuid.uuid4().hex[:10]}"
        mock_rp.create_order.return_value = {
            "id": order_id, 
            "amount": faker.random_int(min=1000, max=50000), 
            "currency": "INR"
        }
        
        response = api_client.post(url, {}, HTTP_TENANT_ID=str(tenant.id))
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["razorpay_order_id"] == order_id

    @patch("payments.views.verification_views.RazorpayService")
    def test_verify_payment(self, mock_rp_class, api_client, tenant, payment, faker):
        url = reverse("verify-payment")
        mock_rp = mock_rp_class.return_value
        mock_rp.verify_payment_signature.return_value = True
        
        data = {
            "razorpay_order_id": payment.razorpay_order_id,
            "razorpay_payment_id": f"pay_{uuid.uuid4().hex[:10]}",
            "razorpay_signature": faker.sha256(),
        }
        response = api_client.post(url, data, HTTP_TENANT_ID=str(tenant.id))
        assert response.status_code == status.HTTP_200_OK

    def test_webhook_ignored(self, api_client, tenant, faker):
        url = reverse("razorpay-webhook")
        data = {"event": "payment.authorized", "id": f"evt_{uuid.uuid4().hex[:10]}", "payload": {}}
        response = api_client.post(url, data, format="json", HTTP_TENANT_ID=str(tenant.id))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "ignored"

    @patch("payments.views.webhook_views.process_webhook_task")
    @patch("payments.views.webhook_views.RazorpayService")
    def test_webhook_captured(self, mock_rp_class, mock_task, api_client, tenant, payment, faker):
        url = reverse("razorpay-webhook")
        mock_rp = mock_rp_class.return_value
        mock_rp.verify_webhook_signature.return_value = True
        
        event_id = f"evt_{uuid.uuid4().hex[:10]}"
        data = {
            "event": "payment.captured",
            "id": event_id,
            "payload": {
                "payment": {
                    "entity": {
                        "id": f"pay_{uuid.uuid4().hex[:10]}",
                        "order_id": payment.razorpay_order_id,
                        "status": "captured"
                    }
                }
            }
        }
        response = api_client.post(
            url, 
            data, 
            format="json", 
            HTTP_X_RAZORPAY_SIGNATURE=faker.sha256(),
            HTTP_TENANT_ID=str(tenant.id)
        )
        assert response.status_code == status.HTTP_202_ACCEPTED
