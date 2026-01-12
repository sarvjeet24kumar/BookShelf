from rest_framework import serializers
from django.db import transaction
from books.models import Book, Genre, BookGenre
from common.enums import RequestStatus, UserRole, Visibility
from django.utils import timezone


class BookListSerializer(serializers.ModelSerializer):
    """Serializer for listing books."""

    genres = serializers.SerializerMethodField()
    created_by = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = [
            "id",
            "title",
            "author",
            "isbn",
            "published_year",
            "request_status",
            "visibility",
            "created_by",
            "genres",
            "created_at",
        ]
        read_only_fields = fields

    def get_genres(self, book):
        """Get list of genre names for this book."""
        return [
            bg.genre.name for bg in book.book_genres.filter(deleted_at__isnull=True)
        ]

    def get_created_by(self, book):
        """Get minimal user info for the creator."""
        if book.created_by:
            return {
                "id": str(book.created_by.id),
                "username": book.created_by.username,
            }
        return None


class BookCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating books."""

    genres = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        help_text="List of genre UUIDs",
    )
    request_status = serializers.ChoiceField(
        choices=RequestStatus.choices,
        required=False,
        help_text="Request status (admin only, defaults to APPROVED)",
    )
    visibility = serializers.ChoiceField(
        choices=Visibility.choices,
        required=False,
        default=Visibility.PUBLIC,
        help_text="Visibility (defaults to PUBLIC)",
    )

    class Meta:
        model = Book
        fields = [
            "title",
            "author",
            "isbn",
            "published_year",
            "visibility",
            "request_status",
            "genres",
        ]

    def validate_genres(self, value):
        """Validate that all genre UUIDs exist."""
        if not value:
            raise serializers.ValidationError("At least one genre is required.")

        existing_genres = Genre.objects.filter(id__in=value, deleted_at__isnull=True)
        if not existing_genres.exists():
            raise serializers.ValidationError("None of the provided genre IDs exist.")

        existing_ids = set(existing_genres.values_list("id", flat=True))
        missing_ids = set(value) - existing_ids
        if missing_ids:
            raise serializers.ValidationError(
                f"Genre IDs not found: {list(missing_ids)}"
            )

        return value

    def validate_isbn(self, value):
        """Check ISBN uniqueness."""
        if Book.objects.filter(isbn=value).exists():
            raise serializers.ValidationError("ISBN already exists.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        genre_ids = validated_data.pop("genres", [])
        request = self.context.get("request")
        user = request.user
        validated_data["created_by"] = user
        if user.role == UserRole.ADMIN:
            if "request_status" not in validated_data:
                validated_data["request_status"] = RequestStatus.APPROVED
        else:
            validated_data["request_status"] = RequestStatus.PENDING

        book = Book.objects.create(**validated_data)

        genres = Genre.objects.filter(id__in=genre_ids)
        for genre in genres:
            BookGenre.objects.create(book=book, genre=genre)

        return book


class BookUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating books (admin only)."""

    genres = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        write_only=True,
        help_text="List of genre UUIDs (replaces existing genres)",
    )

    class Meta:
        model = Book
        fields = [
            "title",
            "author",
            "published_year",
            "request_status",
            "visibility",
            "genres",
        ]
        extra_kwargs = {
            "title": {"required": False},
            "author": {"required": False},
            "published_year": {"required": False},
            "request_status": {"required": False},
            "visibility": {"required": False},
        }

    def validate_request_status(self, value):
        """Validate request_status is a valid choice."""
        valid_statuses = [choice[0] for choice in RequestStatus.choices]
        if value.upper() not in valid_statuses:
            raise serializers.ValidationError(
                f"Invalid status. Allowed: {', '.join(valid_statuses)}"
            )
        return value.upper()

    def validate_genres(self, value):
        """Validate that all genre UUIDs exist."""
        if not value:
            return value

        existing_genres = Genre.objects.filter(id__in=value, deleted_at__isnull=True)
        existing_ids = set(existing_genres.values_list("id", flat=True))
        missing_ids = set(value) - existing_ids

        if missing_ids:
            raise serializers.ValidationError(
                f"Genre IDs not found: {list(missing_ids)}"
            )

        return value

    def update(self, instance, validated_data):
        """Update book and optionally replace genres."""
        genre_ids = validated_data.pop("genres", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save(update_fields=list(validated_data.keys()))

        if genre_ids is not None:
            new_genre_ids = set(genre_ids)
            current_genre_ids = set(
                instance.book_genres.filter(deleted_at__isnull=True)
                .values_list("genre_id", flat=True)
            )
            to_remove = current_genre_ids - new_genre_ids
            if to_remove:
                instance.book_genres.filter(genre_id__in=to_remove).update(
                    deleted_at=timezone.now()
                )

            to_add = new_genre_ids - current_genre_ids
            for genre_id in to_add:
                genre = Genre.objects.get(id=genre_id)
                BookGenre.objects.create(book=instance, genre=genre)

        return instance
