"""
Custom authentication classes for multi-tenancy support.
Handles user authentication, validation, and tenant context setting.
Tenant validation is handled by TenantMiddleware.
"""
import logging
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed
from tenants.context import set_current_tenant

logger = logging.getLogger(__name__)


class TenantAwareJWTAuthentication(JWTAuthentication):
    """
    JWT authentication with user validation and tenant context setting.
    
    Validates:
    - User is not deleted
    - User email is verified
    - User account is active
    
    Also sets tenant context for the request thread.
    """
    
    def authenticate(self, request):
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
