"""
Django signals for automatic cache invalidation.

Invalidates book cache when books or book-genre mappings change.
"""

import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from books.models import Book, BookGenre
from books.tasks import invalidate_book_cache_task

logger = logging.getLogger(__name__)


@receiver([post_save, post_delete], sender=Book)
def invalidate_book_cache_on_change(sender, instance, **kwargs):
    """
    Invalidate cache when book is created, updated, or deleted.
    """
    if instance.tenant_id:
        logger.debug("Signal fired: Book changed, queuing cache invalidation")
        invalidate_book_cache_task.delay(str(instance.tenant_id))


@receiver([post_save, post_delete], sender=BookGenre)
def invalidate_book_cache_on_genre_change(sender, instance, **kwargs):
    """
    Invalidate cache when book-genre mapping changes.
    """
    if instance.book and instance.book.tenant_id:
        logger.debug("Signal fired: BookGenre changed, queuing cache invalidation")
        invalidate_book_cache_task.delay(str(instance.book.tenant_id))
