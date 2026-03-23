from django.db import models
from django.contrib.auth import get_user_model
from common.models import BaseModel
from common.enums import BookStatus
from books.constants import MAX_STATUS_LENGTH

User = get_user_model()


class UserBook(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_books")

    book = models.ForeignKey(
        "Book", on_delete=models.CASCADE, related_name="user_books"
    )

    status = models.CharField(
        max_length=MAX_STATUS_LENGTH,
        choices=BookStatus.choices,
        default=BookStatus.TO_READ,
    )

    class Meta:
        db_table = "user_books"
        constraints = [
            models.UniqueConstraint(fields=["user", "book"], name="unique_user_book")
        ]

    def __str__(self):
        return f"{self.user} → {self.book.title} ({self.status})"
