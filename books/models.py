from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from common.models import BaseModel
from common.enums import BookStatus

User = get_user_model()


class Genre(BaseModel):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        db_table = "genres"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Book(BaseModel):

    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)

    published_year = models.SmallIntegerField(
        validators=[MinValueValidator(1000), MaxValueValidator(2100)],
        null=True,
        blank=True,
    )

    isbn = models.CharField(
        max_length=13,
        unique=True,
    )

    genres = models.ManyToManyField(Genre, through="BookGenre", related_name="books")
    is_active = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "books"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} by {self.author}"


class UserBook(BaseModel):

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_books")

    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="user_books")

    status = models.CharField(
        max_length=20, choices=BookStatus.choices, default=BookStatus.TO_READ
    )

    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "user_books"
        constraints = [
            models.UniqueConstraint(fields=["user", "book"], name="unique_user_book")
        ]

    def __str__(self):
        return f"{self.user} → {self.book.title} ({self.status})"


class BookGenre(BaseModel):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="book_genres")

    genre = models.ForeignKey(
        Genre, on_delete=models.CASCADE, related_name="book_genres"
    )

    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "book_genres"
        constraints = [
            models.UniqueConstraint(fields=["book", "genre"], name="unique_book_genre")
        ]

    def __str__(self):
        return f"{self.book.title} - {self.genre.name}"
