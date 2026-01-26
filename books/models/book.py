from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinLengthValidator
from common.models import TenantAwareModel
from common.enums import RequestStatus
from common.validators import (
    title_validator,
    author_validator,
    isbn_validator,
    published_year_validator,
)
from books.constants import (
    MAX_TITLE_LENGTH,
    MIN_TITLE_LENGTH,
    MAX_AUTHOR_LENGTH,
    MIN_AUTHOR_LENGTH,
    MAX_ISBN_LENGTH,
    MIN_ISBN_LENGTH,
    MAX_STATUS_LENGTH,
)

User = get_user_model()


class Book(TenantAwareModel):
    """
    Book model - extends TenantAwareModel for automatic tenant filtering.
    Inherits: id, created_at, updated_at, deleted_at, tenant, objects manager
    """
    
    title = models.CharField(
        max_length=MAX_TITLE_LENGTH,
        validators=[MinLengthValidator(MIN_TITLE_LENGTH), title_validator],
    )
    author = models.CharField(
        max_length=MAX_AUTHOR_LENGTH,
        validators=[MinLengthValidator(MIN_AUTHOR_LENGTH), author_validator],
    )

    published_year = models.SmallIntegerField(
        validators=[published_year_validator],
    )

    isbn = models.CharField(
        max_length=MAX_ISBN_LENGTH,
        validators=[MinLengthValidator(MIN_ISBN_LENGTH), isbn_validator],
    )

    genres = models.ManyToManyField("Genre", through="BookGenre", related_name="books")
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="created_books",
        null=True,
        blank=True,
    )
    request_status = models.CharField(
        max_length=MAX_STATUS_LENGTH,
        choices=RequestStatus.choices,
        default=RequestStatus.PENDING,
    )

    class Meta:
        db_table = "books"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=['tenant', 'isbn'],
                name='unique_tenant_isbn'
            )
        ]

    def __str__(self):
        return f"{self.title} by {self.author}"
