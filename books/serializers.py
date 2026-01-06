from rest_framework import serializers
from .models import Book, UserBook
from rest_framework import serializers
from django.db import transaction
from .models import Book, Genre, BookGenre


class BookListSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()
    genres = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = [
            "id",
            "title",
            "author",
            "isbn",
            "published_year",
            "status",
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

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        user = self.context["request"].user

        if user.role == "ADMIN":
            representation.pop("status", None)

        return representation


class BookCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    author = serializers.CharField(max_length=255)
    isbn = serializers.CharField(max_length=20)
    published_year = serializers.IntegerField()
    genres = serializers.ListField(child=serializers.CharField(max_length=100))

    def validate_isbn(self, value):
        if Book.objects.filter(isbn=value, deleted_at__isnull=True).exists():
            raise serializers.ValidationError("Book already exists.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        genres = validated_data.pop("genres")

        book = Book.objects.create(**validated_data)

        for genre_name in genres:
            genre, _ = Genre.objects.get_or_create(name=genre_name.strip())

            BookGenre.objects.create(book=book, genre=genre)

        return book
