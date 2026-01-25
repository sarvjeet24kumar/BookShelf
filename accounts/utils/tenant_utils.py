from rest_framework.exceptions import ValidationError as DRFValidationError
from django.core.exceptions import ValidationError as DjangoValidationError
from tenants.models import Tenant


def get_tenant_from_header(request):
    """
    Extract and validate tenant ID from Tenant-ID header.
    Returns Tenant instance.
    Raises ValidationError if header is missing or tenant is invalid.
    """
    tenant_id = request.headers.get("Tenant-ID")
    
    if not tenant_id:
        raise DRFValidationError("Tenant-ID header is required.")
    
    try:
        return Tenant.objects.get(id=tenant_id, is_active=True, deleted_at__isnull=True)
    except (Tenant.DoesNotExist, ValueError, DjangoValidationError):
        raise DRFValidationError("Invalid or inactive tenant.")


def get_optional_tenant_from_header(request):
    """
    Extract and validate tenant ID from Tenant-ID header (optional).
    Returns Tenant instance or None if header is missing.
    Used for login endpoints that support SuperAdmin (no tenant).
    """
    tenant_id = request.headers.get("Tenant-ID")
    
    if not tenant_id:
        return None  # SuperAdmin login allowed without tenant
    
    try:
        return Tenant.objects.get(id=tenant_id, is_active=True, deleted_at__isnull=True)
    except (Tenant.DoesNotExist, ValueError, DjangoValidationError):
        raise DRFValidationError("Invalid or inactive tenant.")
