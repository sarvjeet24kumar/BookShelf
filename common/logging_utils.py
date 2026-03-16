import uuid
import logging
from contextvars import ContextVar
from tenants.context import get_current_tenant

request_id_var = ContextVar("request_id", default=None)
tenant_id_var = ContextVar("tenant_id", default=None)


def generate_request_id():
    """Generate a new UUID-based request ID."""
    return str(uuid.uuid4())


def set_request_id(request_id):
    """Set the request ID for the current context."""
    request_id_var.set(request_id)


def get_request_id():
    """Get the request ID from the current context."""
    return request_id_var.get()


def set_tenant_id(tenant_id):
    """Set the tenant ID for the current context."""
    tenant_id_var.set(tenant_id)


def get_tenant_id():
    """Get the tenant ID from the current context."""
    return tenant_id_var.get()


def clear_context():
    """Clear all context variables. Called after request completion."""
    request_id_var.set(None)
    tenant_id_var.set(None)


class LogContextFilter(logging.Filter):
    """
    Logging filter that automatically injects contextual metadata
    into all log records.
    """

    def filter(self, record):
        """
        Add context variables to the log record.

        """
        record.request_id = get_request_id() or "-"

        tenant_id = get_tenant_id()
        if not tenant_id:
            tenant = get_current_tenant()
            if tenant:
                tenant_id = str(tenant.id)

        record.tenant_id = tenant_id or "-"

        return True
