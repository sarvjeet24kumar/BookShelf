import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import ValidationError
from accounts.serializers.auth_serializers import SignupSerializer, LoginSerializer


logger = logging.getLogger(__name__)


class SignupView(APIView):

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        logger.info("User registered: username=%s", user.username)

        return Response(
            {"message": "Registered Successfully"},
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        refresh = RefreshToken.for_user(user)

        logger.info("User logged in: user_id=%s", user.id)

        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_200_OK,
        )


class LogoutView(APIView):

    def post(self, request):
        refresh_token = request.data.get("refresh")

        if not refresh_token:
            raise ValidationError("Refresh token is required.")

        try:

            token = RefreshToken(refresh_token)
            token.blacklist()

        except TokenError:
            raise ValidationError("Invalid or expired token.")

        logger.info("User logged out: user_id=%s", request.user.id)

        return Response({"message": "Logout successful."}, status=status.HTTP_200_OK)
