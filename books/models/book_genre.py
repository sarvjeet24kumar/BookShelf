from django.db import models
from common.models import BaseModel


class BookGenre(BaseModel):
    book = models.ForeignKey(
        "Book", on_delete=models.CASCADE, related_name="book_genres"
    )

    genre = models.ForeignKey(
        "Genre", on_delete=models.CASCADE, related_name="book_genres"
    )

    class Meta:
        db_table = "book_genres"
        constraints = [
            models.UniqueConstraint(fields=["book", "genre"], name="unique_book_genre")
        ]

    def __str__(self):
        return f"{self.book.title} - {self.genre.name}"
