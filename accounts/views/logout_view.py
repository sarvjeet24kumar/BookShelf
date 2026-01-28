import logging
from datetime import datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from django.core.cache import cache
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

logger = logging.getLogger(__name__)


class LogoutView(APIView):
    """
    Logout endpoint that blacklists both access and refresh tokens.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")

        if not refresh_token:
            raise ValidationError({"refresh": "Refresh token is required."})

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            raise ValidationError({"authorization": "Access token is required ."})

        try:
            raw_access_token = auth_header.split(" ")[1]

            try:
                access_token = AccessToken(raw_access_token)
                jti = access_token.get("jti")
                exp = access_token.get("exp")

                now = datetime.utcnow().timestamp()
                ttl = int(exp - now)

                if ttl > 0:
                    cache.set(f"blacklisted_access_token:{jti}", True, timeout=ttl)
                    logger.info(
                        "Access token blacklisted: user_id=%s, jti=%s, ttl=%ds",
                        request.user.id,
                        jti,
                        ttl,
                    )
            except TokenError as e:
                logger.warning(
                    "Failed to decode access token: user_id=%s, error=%s",
                    request.user.id,
                    str(e),
                )

            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
                logger.info("Refresh token blacklisted: user_id=%s", request.user.id)
            except TokenError as e:
                raise ValidationError({"refresh": "Invalid or expired refresh token."})

            logger.info("User logged out successfully: user_id=%s", request.user.id)
            return Response({"detail": "Logged out successfully"})

        except ValidationError:
            raise
        except Exception as e:
            logger.exception(f"Unexpected logout error: {str(e)}")
            raise ValidationError({"detail": "Logout failed. Please try again."})
