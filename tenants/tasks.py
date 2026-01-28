import logging
from celery import shared_task
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from tenants.models import Tenant
from tenants.context import TenantContext
from accounts.models import User
from books.models import Book, Genre
from payments.models import Payment, Subscription
    

logger = logging.getLogger(__name__)


@shared_task
def cleanup_deleted_tenants():
    """
    Hard delete related data after retention period but keep the tenant record.
    
    """

    retention_days = getattr(settings, 'TENANT_DATA_RETENTION_DAYS', 30)
    cutoff_date = timezone.now() - timedelta(days=retention_days)
    
    tenants_to_purge = Tenant.all_objects.filter(
        deleted_at__lt=cutoff_date,
        deleted_at__isnull=False
    )
    
    purged_count = 0
    
    for tenant in tenants_to_purge:
        tenant_slug = tenant.slug
        tenant_id = tenant.id
        
        try:
            with TenantContext(tenant):
                User.all_objects.filter(tenant=tenant).delete()
                Book.all_objects.filter(tenant=tenant).delete()
                Genre.all_objects.filter(tenant=tenant).delete()
                Payment.all_objects.filter(tenant=tenant).delete()
                Subscription.objects.filter(tenant=tenant).delete()
            
            purged_count += 1
            
            logger.info(
                "Successfully purged all data for tenant: slug=%s, id=%s. "
                "Tenant record remains in database.",
                tenant_slug,
                tenant_id
            )
            
        except Exception as e:
            logger.error(
                "Failed to purge data for tenant: slug=%s, id=%s, error=%s",
                tenant_slug,
                tenant_id,
                str(e)
            )
    
    logger.info(
        "Tenant cleanup complete: %d tenants purged (retention: %d days)",
        purged_count,
        retention_days
    )
    
    return f"Purged data for {purged_count} tenants"
