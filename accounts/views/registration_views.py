import logging
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.exceptions import ValidationError
from common.throttling import IPThrottle, AuthThrottle
from accounts.serializers.auth_serializers import SignupSerializer
from accounts.services import email_verification_service
from accounts.utils.tenant_utils import get_tenant_from_header

logger = logging.getLogger(__name__)
User = get_user_model()


class SignupView(APIView):
    """
    Handle user signup with email verification.

    """

    permission_classes = [AllowAny]
    throttle_classes = [IPThrottle, AuthThrottle]

    def post(self, request):
        tenant = get_tenant_from_header(request)
        serializer = SignupSerializer(
            data=request.data, context={"tenant_id": tenant.id}
        )
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]

        existing_user = User.all_objects.filter(
            email=email, tenant_id=tenant.id
        ).first()

        if existing_user:
            raise ValidationError(
                "An account with this email cannot be created. Please contact support."
            )

        user = serializer.save(tenant=tenant)

        email_verification_service.create(
            user.username, user.email, tenant_id=str(tenant.id)
        )
        logger.info("Signup completed successfully")

        return Response(
            {"detail": "Verification code sent to your email."},
            status=status.HTTP_200_OK,
        )
