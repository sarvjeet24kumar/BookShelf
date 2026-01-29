import logging
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.exceptions import ValidationError
from common.throttling import IPThrottle, AuthThrottle
from accounts.services import email_verification_service
from accounts.utils.tenant_utils import get_tenant_from_header
from accounts.utils.user_lookup import find_user_with_validation


logger = logging.getLogger(__name__)
User = get_user_model()


class VerifyEmailView(APIView):
    """
    Verify email with OTP using email or username.
    """

    permission_classes = [AllowAny]
    throttle_classes = [IPThrottle, AuthThrottle]

    def post(self, request):

        tenant = get_tenant_from_header(request)
        email = request.data.get("email", "").strip().lower()
        username = request.data.get("username", "").strip().lower()
        otp = request.data.get("otp", "").strip()

        user = find_user_with_validation(
            email=email, username=username, tenant=tenant, require_otp=True, otp=otp
        )

        if not user:
            raise ValidationError("No pending signup found.")

        if user.is_email_verified:
            raise ValidationError("Email already verified. Please login.")

        tenant_id_str = str(tenant.id)

        success, error = email_verification_service.verify(
            user.username, otp, tenant_id=tenant_id_str
        )
        if not success:
            raise ValidationError(error)

        user.is_email_verified = True
        user.is_active = True
        user.save(update_fields=["is_email_verified", "is_active", "updated_at"])

        email_verification_service.cleanup(user.username, tenant_id=tenant_id_str)
        logger.info("Email verified: user_id=%s, username=%s", user.id, user.username)

        return Response(
            {"detail": "Email verified. Account activated successfully."},
            status=status.HTTP_201_CREATED,
        )


class ResendOTPView(APIView):
    """
    Resend OTP for email verification using email or username.
    """

    permission_classes = [AllowAny]
    throttle_classes = [IPThrottle, AuthThrottle]

    def post(self, request):

        tenant = get_tenant_from_header(request)
        email = request.data.get("email", "").strip().lower()
        username = request.data.get("username", "").strip().lower()

        user = find_user_with_validation(email=email, username=username, tenant=tenant)

        if not user:
            return Response(
                {"detail": "New verification code sent to your email."},
                status=status.HTTP_200_OK,
            )

        if user.is_email_verified:
            raise ValidationError("Email already verified. Please login.")

        tenant_id_str = str(tenant.id)

        email_verification_service.create(
            user.username, user.email, tenant_id=tenant_id_str
        )
        logger.info("OTP resent: username=%s", user.username)

        return Response(
            {"detail": "New verification code sent to your email."},
            status=status.HTTP_200_OK,
        )
