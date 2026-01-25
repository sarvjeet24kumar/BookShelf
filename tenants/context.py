from threading import local

_thread_locals = local()


def set_current_tenant(tenant):
    """
    Set the current tenant for this request thread.
    """
    _thread_locals.tenant = tenant


def get_current_tenant():
    """
    Get the current tenant for this request thread.
    """
    return getattr(_thread_locals, 'tenant', None)


def clear_current_tenant():
    """
    Clear the current tenant at end of request.
    """
    if hasattr(_thread_locals, 'tenant'):
        del _thread_locals.tenant
