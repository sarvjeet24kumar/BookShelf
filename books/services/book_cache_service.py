import logging
from typing import Optional, List
from django.core.cache import cache
from django.db.models import QuerySet
from common.enums import UserRole

logger = logging.getLogger(__name__)

CACHE_TTL = 900
CACHE_PREFIX = "tenant"


class BookCacheService:
    """
    Service for caching tenant book lists in Redis.
    
    """

    @staticmethod
    def _get_cache_key(tenant_id, status):
        """Generate cache key for tenant books."""
        if status:
            return f"{CACHE_PREFIX}:{tenant_id}:books:{status}"
        return f"{CACHE_PREFIX}:{tenant_id}:books:all"

    @staticmethod
    def get_books_for_tenant(tenant_id, status):
        """
        Get cached book list for tenant.

        """
        cache_key = BookCacheService._get_cache_key(tenant_id, status)
        cached_data = cache.get(cache_key)

        if cached_data:
            logger.debug("Cache HIT")
            return cached_data

        logger.debug("Cache MISS")
        return None

    @staticmethod
    def set_books_cache(tenant_id, books_queryset, status):
        """
        Store book list in cache.
        """
        cache_key = BookCacheService._get_cache_key(tenant_id, status)

        from books.serializers import BookListSerializer

        exclude_fields = []
        if status != UserRole.ADMIN.lower():
            exclude_fields.append("deleted_at")
        serializer = BookListSerializer(
            books_queryset, many=True, exclude_fields=exclude_fields
        )
        books_data = serializer.data

        cache.set(cache_key, books_data, timeout=CACHE_TTL)
        logger.info(
            f"Cached {len(books_data)} books (TTL={CACHE_TTL}s)"
        )

    @staticmethod
    def invalidate_tenant_books(tenant_id):
        """
        Invalidate all book caches for a tenant.
        """
        cache_keys = [
            BookCacheService._get_cache_key(tenant_id, None),
            BookCacheService._get_cache_key(tenant_id, "admin"),
            BookCacheService._get_cache_key(tenant_id, "user"),
        ]

        cache.delete_many(cache_keys)
        logger.info("Invalidated book cache")


book_cache_service = BookCacheService()
