import logging
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework.exceptions import AuthenticationFailed
from django.core.cache import cache
from tenants.context import set_current_tenant
from accounts.models import User

logger = logging.getLogger(__name__)


class TenantAwareJWTAuthentication(JWTAuthentication):
    """
    Custom JWT authentication that:
    """

    def get_validated_token(self, raw_token):
        """
        Validate token and check if it's blacklisted.
        """
        validated_token = super().get_validated_token(raw_token)
        jti = validated_token.get("jti")
        if cache.get(f"blacklisted_access_token:{jti}"):
            raise InvalidToken("Invalid token", code="token_not_valid")

        return validated_token

    def get_user(self, validated_token):
        """
        Optimize: Fetch user and tenant in a single query.
        """

        try:
            user_id = validated_token["user_id"]
            user = User.objects.select_related("tenant").get(id=user_id)
        except (User.DoesNotExist, KeyError):
            raise InvalidToken("User not found", code="user_not_found")

        return user

    def authenticate(self, request):
        """Authenticate and set tenant context."""
        result = super().authenticate(request)

        if result is not None:
            user, token = result

            if user.deleted_at is not None:
                logger.warning(
                    "Blocked API access for deleted user",
                )
                raise AuthenticationFailed(
                    "This account has been deleted. Please contact support for assistance."
                )

            if not user.is_email_verified:
                logger.warning(
                    "Blocked API access for unverified user",
                )
                raise AuthenticationFailed(
                    "Please verify your email before accessing the application."
                )

            if not user.is_active:
                logger.warning("Blocked API access for inactive user")
                raise AuthenticationFailed(
                    "This account has been suspended. Please contact support for assistance."
                )

            tenant = getattr(user, "tenant", None)

            if tenant:

                if tenant.deleted_at is not None:
                    logger.warning("Blocked API access for deleted tenant")
                    raise AuthenticationFailed(
                        "Your organization's account has been deleted. "
                        "Please contact support for assistance."
                    )

                if not tenant.is_active:
                    logger.warning("Blocked API access for suspended tenant")
                    raise AuthenticationFailed(
                        "Your organization's account has been suspended. "
                        "Please contact support for assistance."
                    )

            set_current_tenant(tenant)

            if tenant:
                logger.debug("Tenant context set")
            else:
                logger.debug("No tenant context set (SuperAdmin access)")

        return result
