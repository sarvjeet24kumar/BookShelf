import logging
from rest_framework.authentication import SessionAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

logger = logging.getLogger(__name__)


class CsrfExemptSessionAuthentication(SessionAuthentication):
    """
    Session authentication that skips CSRF for safe HTTP methods.

    """

    def enforce_csrf(self, request):
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return
        super().enforce_csrf(request)


class JWTQueryParamAuthentication(JWTAuthentication):
    """
    JWT Authentication that reads token from URL query parameter.
    """

    def authenticate(self, request):
        token = request.query_params.get("token")

        if not token:
            return None

        try:
            validated_token = self.get_validated_token(token)
            user = self.get_user(validated_token)
            logger.debug("JWT query param auth successful")
            return (user, validated_token)
        except (InvalidToken, TokenError) as e:
            logger.warning(f"JWT query param auth failed: {str(e)}")
            return None
