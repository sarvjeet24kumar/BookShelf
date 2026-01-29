import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.core.cache import cache
from common.enums import UserRole
from accounts.tasks import seed_tenant_task

User = get_user_model()
logger = logging.getLogger(__name__)


def is_tenant_seeded(tenant_id):
    """Check if tenant has already been seeded."""
    cache_key = f"tenant_seeded:{tenant_id}"
    return cache.get(cache_key, False)


@receiver(post_save, sender=User)
def auto_seed_tenant_on_first_admin(sender, instance, created, **kwargs):
    """
    Automatically run seed.py when tenant's first admin is created.

    """
    if not created:
        return
    
    if instance.role != UserRole.ADMIN:
        return

    if instance.tenant is None:
        logger.debug(f"Skipping seeding for global superadmin: {instance.username}")
        return
    
    if is_tenant_seeded(instance.tenant.id):
        logger.info(f"Tenant {instance.tenant.slug} already seeded")
        return
    
    logger.info(
        f"Queuing auto-seeding for tenant: tenant={instance.tenant.slug}, admin={instance.username}"
    )
    
    try:
        seed_tenant_task.delay(str(instance.tenant.id), str(instance.id))
        logger.info(f"Tenant {instance.tenant.slug} seeding task queued")
    except Exception as e:
        logger.exception(f"Failed to queue seeding for tenant {instance.tenant.id}: {str(e)}")

