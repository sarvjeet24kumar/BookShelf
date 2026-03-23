from django.db import models
from common.models import TenantAwareModel
from books.constants import MAX_GENRE_NAME_LENGTH


class Genre(TenantAwareModel):
    """
    Genre model - extends TenantAwareModel for automatic tenant filtering.
    Inherits: id, created_at, updated_at, deleted_at, tenant, objects manager
    """

    name = models.CharField(max_length=MAX_GENRE_NAME_LENGTH)
    description = models.TextField(blank=True, default="")

    class Meta:
        db_table = "genres"
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "name"], name="unique_tenant_genre"
            )
        ]

    def __str__(self):
        return self.name
