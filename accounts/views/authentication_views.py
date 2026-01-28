import logging
from django.contrib.auth import authenticate, get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import ValidationError, AuthenticationFailed
from common.throttling import IPThrottle, AuthThrottle
from accounts.serializers.auth_serializers import LoginSerializer
from accounts.services import login_otp_service
from accounts.utils.tenant_utils import get_tenant_from_header
from accounts.utils.user_lookup import find_user_with_validation,find_user

logger = logging.getLogger(__name__)
User = get_user_model()


class LoginView(APIView):
    """
    MFA login : Validate credentials and send OTP.
    """

    permission_classes = [AllowAny]
    throttle_classes = [IPThrottle, AuthThrottle]

    def post(self, request):
        tenant = get_tenant_from_header(request, required=False) 

        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data.get("email")
        username = serializer.validated_data.get("username")
        password = serializer.validated_data.get("password")

        user = find_user(email=email, username=username, tenant=tenant)

        if not user:
            raise AuthenticationFailed("Invalid credentials.")

        if user.deleted_at:
            raise AuthenticationFailed(
                "This account has been deleted. Please contact support."
            )
        if not user.is_email_verified:
            raise AuthenticationFailed("Please verify your email before logging in.")
        if not user.is_active:
            raise AuthenticationFailed(
                "This account has been suspended. Please contact support."
            )
        authenticated_user = authenticate(
            request=request, username=user.username, password=password
        )

        if not authenticated_user:
            raise AuthenticationFailed("Invalid credentials.")

        tenant_id = str(user.tenant_id) if user.tenant else None
        login_otp_service.create(user.username, user.email, tenant_id=tenant_id)
        logger.info("Login OTP sent: user_id=%s, username=%s", user.id, user.username)

        return Response(
            {
                "detail": "OTP sent to your email. Please verify to complete login.",
            }
        )


class VerifyLoginView(APIView):
    """
    MFA login: Verify OTP using email or username.
    """

    permission_classes = [AllowAny]
    throttle_classes = [IPThrottle, AuthThrottle]

    def post(self, request):
        tenant = get_tenant_from_header(request, required=False)
        email = request.data.get("email", "").strip().lower()
        username = request.data.get("username", "").strip().lower()
        otp = request.data.get("otp", "").strip()
    
        user = find_user_with_validation(
            email=email, 
            username=username, 
            tenant=tenant, 
            require_otp=True, 
            otp=otp
        )

        if not user:
            raise ValidationError("Invalid credentials or OTP.")


        tenant_id = str(user.tenant_id) if user.tenant else None
        is_valid, error_msg = login_otp_service.verify(
            user.username, otp, tenant_id=tenant_id
        )

        if not is_valid:
            raise ValidationError(error_msg)

        login_otp_service.cleanup(user.username, tenant_id=tenant_id)

        refresh = RefreshToken.for_user(user)
        logger.info("User logged in: user_id=%s, username=%s", user.id, user.username)

        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            }
        )

