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
        try:
            serializer = SignupSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            user = serializer.save()

            logger.info("User registered: username=%s", user.username)

            return Response(
                {"message": "Registered Successfully"},
                status=status.HTTP_201_CREATED,
            )

        except ValidationError as e:
            return Response(
                {"errors": e.detail},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception:
            logger.exception("Signup failed for username: %s", request.data.get("username", "unknown"))
            return Response(
                {"error": "Something went wrong. Please try again later."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class LoginView(APIView):

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)

        if serializer.is_valid():
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
        logger.warning(
            "Failed login attempt: username=%s", request.data.get("username", "unknown")
        )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")

            if not refresh_token:
                return Response(
                    {"error": "Refresh token is required."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            token = RefreshToken(refresh_token)
            token.blacklist()

            logger.info("User logged out: user_id=%s", request.user.id)

            return Response(
                {"message": "Logout successful."}, status=status.HTTP_200_OK
            )

        except TokenError:
            return Response(
                {"error": "Invalid or expired token."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception:
            logger.exception("Logout failed for user: %s", request.user.id)
            return Response(
                {"error": "An error occurred during logout."},
                status=status.HTTP_400_BAD_REQUEST,
            )
