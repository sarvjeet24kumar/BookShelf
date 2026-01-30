import logging
from rest_framework.exceptions import AuthenticationFailed
from tenants.context import  clear_current_tenant

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
