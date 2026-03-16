import logging
from django.contrib.auth import get_user_model
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.exceptions import ValidationError
from common.throttling import IPThrottle, AuthThrottle
from accounts.services import password_reset_service
from accounts.utils.tenant_utils import get_tenant_from_header
from accounts.utils.user_lookup import find_user_with_validation

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

        tenant = get_tenant_from_header(request, required=False)
        email = request.data.get("email", "").strip().lower()
        username = request.data.get("username", "").strip().lower()

        user = find_user_with_validation(email=email, username=username, tenant=tenant)

        if not user:
            return Response(
                {
                    "detail": "If an account exists, a reset link has been sent to the registered email."
                }
            )

        tenant_id = str(user.tenant_id) if user.tenant else None
        password_reset_service.create(
            user.username, user.id, user.email, tenant_id=tenant_id
        )
        logger.info("Password reset initiated")

        return Response(
            {
                "detail": "If an account exists, a reset link has been sent to the registered email."
            }
        )


class ResetPasswordView(APIView):

    permission_classes = [AllowAny]
    throttle_classes = [IPThrottle, AuthThrottle]

    def get(self, request):
        token = request.GET.get("token")
        if not token:
            return render(
                request,
                "accounts/reset_password.html",
                {"error": "Missing or invalid token."},
            )

        success, error, user_id = password_reset_service.verify(token)
        if not success:
            return render(request, "accounts/reset_password.html", {"error": error})

        return render(request, "accounts/reset_password.html", {"token": token})

    def post(self, request):
        token = request.GET.get("token") or request.data.get("token")
        password = request.data.get("password")
        confirm_password = request.data.get("confirm_password")

        if not token:
            return render(
                request,
                "accounts/reset_password.html",
                {"form_error": "Reset token is required."},
            )
        if not password or not confirm_password:
            return render(
                request,
                "accounts/reset_password.html",
                {"form_error": "Both password and confirmation are required."},
            )
        if password != confirm_password:
            return render(
                request,
                "accounts/reset_password.html",
                {"form_error": "Passwords do not match."},
            )

        success, error, user_id = password_reset_service.verify(token)
        if not success:
            return render(
                request, "accounts/reset_password.html", {"form_error": error}
            )

        user = User.all_objects.filter(id=user_id).first()
        if not user:
            return render(
                request,
                "accounts/reset_password.html",
                {"form_error": "User not found."},
            )

        user.set_password(password)
        user.save(update_fields=["password", "updated_at"])

        password_reset_service.cleanup(token)
        logger.info("Password reset successful")

        return render(request, "accounts/reset_password.html", {"success": True})
