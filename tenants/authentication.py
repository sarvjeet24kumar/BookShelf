"""
Custom authentication classes for multi-tenancy support.
Handles user authentication, validation, and tenant context setting.
Tenant validation is handled by TenantMiddleware.
"""
import logging
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework.exceptions import AuthenticationFailed
from django.core.cache import cache
from tenants.context import set_current_tenant

logger = logging.getLogger(__name__)


class TenantAwareJWTAuthentication(JWTAuthentication):
    """
    Custom JWT authentication that:
    1. Checks if access token is blacklisted (logout invalidation)
    2. Sets tenant context from the authenticated user
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

    def authenticate(self, request):
        """Authenticate and set tenant context."""
        result = super().authenticate(request)
        
        if result is not None:
            user, token = result
            

            if user.deleted_at is not None:
                logger.warning(
                    "Blocked API access for deleted user: user_id=%s, email=%s",
                    user.id,
                    user.email
                )
                raise AuthenticationFailed(
                    "This account has been deleted. Please contact support for assistance."
                )
            

            if not user.is_email_verified:
                logger.warning(
                    "Blocked API access for unverified user: user_id=%s, email=%s",
                    user.id,
                    user.email
                )
                raise AuthenticationFailed(
                    "Please verify your email before accessing the application."
                )
            

            if not user.is_active:
                logger.warning(
                    "Blocked API access for inactive user: user_id=%s, email=%s",
                    user.id,
                    user.email
                )
                raise AuthenticationFailed(
                    "This account has been suspended. Please contact support for assistance."
                )
            

            tenant = getattr(user, 'tenant', None)
            set_current_tenant(tenant)
            
            if tenant:
                logger.debug("Tenant context set: %s (user: %s)", tenant.slug, user.email)
            else:
                logger.debug("No tenant context set (SuperAdmin: %s)", user.email)
        
        return result
