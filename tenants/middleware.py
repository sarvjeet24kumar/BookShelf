import logging
from rest_framework.exceptions import AuthenticationFailed
from tenants.context import set_current_tenant, clear_current_tenant

logger = logging.getLogger(__name__)


class TenantMiddleware:
    """
    Middleware to set tenant context and validate tenant status.

    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        clear_current_tenant()
        
        response = self.get_response(request)
        
        clear_current_tenant()
        
        return response
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        """
        Run after authentication but before view.
        Sets tenant context and validates tenant status.
        """

        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return None
        
        user = request.user
        tenant = getattr(user, 'tenant', None)
        

        if tenant:
            tenant.refresh_from_db()
            
            logger.info(
                "Tenant check: tenant_id=%s, deleted_at=%s, is_active=%s",
                tenant.id,
                tenant.deleted_at,
                tenant.is_active
            )
            
            if tenant.deleted_at is not None:
                logger.warning(
                    "Blocked request from deleted tenant: tenant_id=%s, user_id=%s, path=%s",
                    tenant.id,
                    user.id,
                    request.path
                )
                raise AuthenticationFailed(
                    "Your organization's account has been deleted. "
                    "Please contact support for assistance."
                )
            
            if not tenant.is_active:
                logger.warning(
                    "Blocked request from suspended tenant: tenant_id=%s, user_id=%s, path=%s",
                    tenant.id,
                    user.id,
                    request.path
                )
                raise AuthenticationFailed(
                    "Your organization's account has been suspended. "
                    "Please contact support for assistance."
                )
            

            set_current_tenant(tenant)
            logger.debug("Tenant context set: %s (user: %s)", tenant.slug, user.email)
        else:

            set_current_tenant(None)
            logger.debug("No tenant context (SuperAdmin)")
        
        return None
