import logging
from celery import shared_task
from books.services.book_cache_service import book_cache_service

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 10},
)
def invalidate_book_cache_task(self, tenant_id: str):
    """
    Asynchronous task to invalidate book cache for a tenant.
    """
    logger.info(f"Executing Celery task: Invalidate book cache for tenant {tenant_id}")
    try:
        book_cache_service.invalidate_tenant_books(tenant_id)
        logger.info(f"Successfully invalidated cache for tenant {tenant_id}")
    except Exception as e:
        logger.error(f"Error invalidating cache for tenant {tenant_id}: {str(e)}")
        raise e
