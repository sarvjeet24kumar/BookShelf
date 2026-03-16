from rest_framework.exceptions import ValidationError as DRFValidationError
from django.core.exceptions import ValidationError as DjangoValidationError
from tenants.models import Tenant


def get_tenant_from_header(request, required=True):
    """
    Extract and validate tenant ID from Tenant-ID header.

    """
    tenant_id = request.headers.get("Tenant-ID")

    if not tenant_id:
        if required:
            raise DRFValidationError("Tenant-ID header is required.")
        return None

    try:
        return Tenant.objects.get(id=tenant_id, is_active=True, deleted_at__isnull=True)
    except (Tenant.DoesNotExist, ValueError, DjangoValidationError):
        raise DRFValidationError("Invalid or inactive tenant.")
