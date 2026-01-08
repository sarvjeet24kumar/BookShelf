import re
import uuid
from rest_framework import serializers
from django.db import transaction
from .models import Book, Genre, BookGenre, UserBook


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ["id", "name", "created_at"]


class BookListSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()
    genres = serializers.SerializerMethodField()
    created_by_email = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = [
            "id",
            "title",
            "author",
            "isbn",
            "published_year",
            "status",
            "request_status",
            "created_by_email",
            "genres",
            "created_at",
        ]

    def get_status(self, book):
        user = self.context["request"].user

        user_book = UserBook.objects.filter(
            user=user, book=book, deleted_at__isnull=True
        ).first()

        return user_book.status if user_book else None

    def get_genres(self, book):
        return [
            bg.genre.name for bg in book.book_genres.filter(deleted_at__isnull=True)
        ]

    def get_created_by_email(self, book):
        if book.created_by:
            return book.created_by.email
        return None

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        request = self.context.get("request")

        if request and request.resolver_match.view_name == "my-books":
            representation.pop("request_status", None)
        else:
            representation.pop("status", None)

        return representation


class BookValidationMixin:

    TEXT_PATTERN = r"^[a-zA-Z0-9\s_'.,]+$"

    def validate_title(self, value):

        value = value.strip()

        if not re.search(r"[a-zA-Z]", value):
            raise serializers.ValidationError("Title must contain at least one letter.")

        if not re.match(self.TEXT_PATTERN, value):
            raise serializers.ValidationError(
                "Title can only contain letters, numbers, spaces, underscores, apostrophes, periods, and commas."
            )
        return value

    def validate_author(self, value):

        value = value.strip()

        if not re.search(r"[a-zA-Z]", value):
            raise serializers.ValidationError(
                "Author must contain at least one letter."
            )

        if not re.match(self.TEXT_PATTERN, value):
            raise serializers.ValidationError(
                "Author can only contain letters, numbers, spaces, underscores, apostrophes, periods, and commas."
            )
        return value

    def validate_published_year(self, value):
      
        if value < 1000 or value > 2100:
            raise serializers.ValidationError(
                "Published year must be between 1000 and 2100."
            )
        return value

    def validate_genres_data(self, genre_ids):
       
        valid_genre_uuids = []
        invalid_genre_ids = []

        for genre_id in genre_ids:
            try:
                genre_uuid = uuid.UUID(str(genre_id))
                valid_genre_uuids.append(genre_uuid)
            except (ValueError, TypeError, AttributeError):
                invalid_genre_ids.append(genre_id)

        if len(valid_genre_uuids) == 0:
            raise serializers.ValidationError(
                {
                    "genres": "No valid genre IDs provided. Please provide at least one valid genre UUID."
                }
            )

        existing_genres = Genre.objects.filter(id__in=valid_genre_uuids)
        if not existing_genres.exists():
            raise serializers.ValidationError(
                {
                    "genres": "None of the provided genre IDs exist in the database. Please provide at least one valid existing genre."
                }
            )

        return list(existing_genres.values_list("id", flat=True)), invalid_genre_ids


class BookCreateSerializer(BookValidationMixin, serializers.Serializer):
    title = serializers.CharField(max_length=255)
    author = serializers.CharField(max_length=255)
    isbn = serializers.CharField(max_length=13)
    published_year = serializers.IntegerField()
    genres = serializers.ListField(child=serializers.CharField(max_length=100))

    def validate(self, attrs):
        isbn = attrs.get("isbn")
        if len(isbn) > 13:
            raise serializers.ValidationError(
                {"error": "ISBN cannot be more than 13 characters."}
            )

        if Book.objects.filter(isbn=isbn).exists():
            raise serializers.ValidationError({"isbn": "ISBN already exists."})

      
        genre_ids = attrs.get("genres", [])
        existing_genre_ids, invalid_genre_ids = self.validate_genres_data(genre_ids)

        attrs["existing_genre_ids"] = existing_genre_ids
        attrs["invalid_genre_ids"] = invalid_genre_ids

        return super().validate(attrs)

    @transaction.atomic
    def create(self, validated_data):
        existing_genre_ids = validated_data.pop("existing_genre_ids", [])
        validated_data.pop("invalid_genre_ids", None)
        validated_data.pop("genres", None)

        request = self.context.get("request")
        if request and hasattr(request, "user"):
            validated_data["created_by"] = request.user
            if request.user.role == "ADMIN":
                validated_data["request_status"] = "APPROVED"

        book = Book.objects.create(**validated_data)

        existing_genres = Genre.objects.filter(id__in=existing_genre_ids)
        for genre in existing_genres:

            BookGenre.objects.create(book=book, genre=genre)

        return book


class BookUpdateSerializer(BookValidationMixin, serializers.Serializer):

    title = serializers.CharField(max_length=255, required=False)
    author = serializers.CharField(max_length=255, required=False)
    published_year = serializers.IntegerField(required=False)
    request_status = serializers.CharField(max_length=20, required=False)

    def validate_request_status(self, value):
    
        from common.enums import RequestStatus

        new_status = value.upper()
        valid_statuses = [choice[0] for choice in RequestStatus.choices]

        if new_status not in valid_statuses:
            raise serializers.ValidationError(
                f"Invalid status. Allowed values are: {', '.join(valid_statuses)}"
            )
        return new_status

    def update(self, instance, validated_data):
    
        # Update allowed fields only (ISBN and genres are not updateable)
        instance.title = validated_data.get("title", instance.title)
        instance.author = validated_data.get("author", instance.author)
        instance.published_year = validated_data.get(
            "published_year", instance.published_year
        )
        instance.request_status = validated_data.get(
            "request_status", instance.request_status
        )

        instance.save()
        return instance
