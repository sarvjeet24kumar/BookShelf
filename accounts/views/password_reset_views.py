import logging
from django.contrib.auth import get_user_model
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.exceptions import ValidationError
from common.throttling import IPThrottle, AuthThrottle
from accounts.services import password_reset_service
from accounts.utils.tenant_utils import get_optional_tenant_from_header


logger = logging.getLogger(__name__)
User = get_user_model()


class ForgotPasswordView(APIView):
    """
    Initiate password reset flow by sending a link to user's email.
    Uses email or username to identify the user.
  
    """
    permission_classes = [AllowAny]
    throttle_classes = [IPThrottle, AuthThrottle]

    def post(self, request):
        tenant = get_optional_tenant_from_header(request)
        email = request.data.get("email", "").strip().lower()
        username = request.data.get("username", "").strip().lower()
        
        if email and username:
            raise ValidationError("Provide either email or username, not both.")
        if not email and not username:
            raise ValidationError("Email or username is required.")
        
        if username:
            if tenant:  
                user = User.all_objects.filter(username=username, tenant_id=tenant.id).first()
            else:
                user = User.all_objects.filter(username=username, tenant_id__isnull=True).first()
        else:
            if tenant:
                user = User.all_objects.filter(email=email, tenant_id=tenant.id).first()
            else:
                user = User.all_objects.filter(email=email, tenant_id__isnull=True).first()
        
        if not user:
            return Response({
                "detail": "If an account exists, a reset link has been sent to the registered email."
            })
        
        tenant_id = str(user.tenant_id) if user.tenant else None
        password_reset_service.create(user.username, user.id, user.email, tenant_id=tenant_id)
        logger.info("Password reset initiated: user_id=%s", user.id)
        
        return Response({
            "detail": "If an account exists, a reset link has been sent to the registered email."
        })



class ResetPasswordView(APIView):
    """
    Show reset password form (GET) and update password (POST).
  
    """
    permission_classes = [AllowAny]
    throttle_classes = [IPThrottle, AuthThrottle]

    def get(self, request):
        token = request.GET.get("token")
        if not token:
            return render(request, "accounts/reset_password.html", {"error": "Missing or invalid token."})

        success, error, user_id = password_reset_service.verify(token)
        if not success:
            return render(request, "accounts/reset_password.html", {"error": error})
        
        return render(request, "accounts/reset_password.html", {"token": token})

    def post(self, request):
        token = request.GET.get("token") or request.data.get("token")
        password = request.data.get("password")
        confirm_password = request.data.get("confirm_password")
        
        if not token:
            raise ValidationError("Reset token is required.")
        if not password or not confirm_password:
            raise ValidationError("Both password and confirmation are required.")
        if password != confirm_password:
            raise ValidationError("Passwords do not match.")
        
        success, error, user_id = password_reset_service.verify(token)
        if not success:
            raise ValidationError(error)
        
        user = User.all_objects.filter(id=user_id).first()
        if not user:
            raise ValidationError("User not found.")
        
        user.set_password(password)
        user.save(update_fields=["password", "updated_at"])
        
        password_reset_service.cleanup(token)
        logger.info("Password reset successful: user_id=%s", user.id)
        
        return Response({"detail": "Password successfully reset."})
