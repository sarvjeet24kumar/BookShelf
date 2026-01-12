from rest_framework import serializers
from books.models import Book, UserBook
from common.enums import BookStatus


class MyBookListSerializer(serializers.ModelSerializer):
    """Serializer for listing user's books (my-books endpoint)."""

    genres = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    added_at = serializers.SerializerMethodField()
    created_by = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = [
            "id",
            "title",
            "author",
            "isbn",
            "published_year",
            "status",
            "added_at",
            "created_by",
            "genres",
            "created_at",
        ]
        read_only_fields = fields

    def _get_user_book(self, book):
        """Helper to get UserBook for current user."""
        if not hasattr(self, "_user_book_cache"):
            self._user_book_cache = {}
        
        if book.id not in self._user_book_cache:
            user = self.context["request"].user
            self._user_book_cache[book.id] = UserBook.objects.filter(
                user=user, book=book, deleted_at__isnull=True
            ).first()
        
        return self._user_book_cache[book.id]

    def get_genres(self, book):
        """Get list of genre names for this book."""
        return [
            bg.genre.name for bg in book.book_genres.filter(deleted_at__isnull=True)
        ]

    def get_status(self, book):
        """Get user's reading status for this book."""
        user_book = self._get_user_book(book)
        return user_book.status if user_book else None

    def get_added_at(self, book):
        """Get when user added this book to library."""
        user_book = self._get_user_book(book)
        return user_book.created_at if user_book else None

    def get_created_by(self, book):
        """Get user who added this book to the platform."""
        if book.created_by:
            return {
                "id": str(book.created_by.id),
                "username": book.created_by.username,
            }
        return None


class MyBookAddSerializer(serializers.Serializer):
    """Serializer for adding a book to user's library."""

    book_id = serializers.UUIDField(
        help_text="UUID of the book to add"
    )
    status = serializers.ChoiceField(
        choices=BookStatus.choices,
        default=BookStatus.TO_READ,
        help_text="Initial reading status (defaults to TO_READ)",
    )


class MyBookUpdateSerializer(serializers.Serializer):
    """Serializer for updating reading status in user's library."""

    status = serializers.ChoiceField(
        choices=BookStatus.choices,
        help_text="Reading status (TO_READ, READING, COMPLETED)",
    )
