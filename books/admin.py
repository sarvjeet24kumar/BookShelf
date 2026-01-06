from django.contrib import admin
from .models import Book, Genre, UserBook, BookGenre


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "created_at")
    search_fields = ("name",)


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "author",
        "isbn",
        "published_year",
        "created_at",
    )

    search_fields = ("title", "author", "isbn")
    ordering = ("-created_at",)


@admin.register(UserBook)
class UserBookAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "book",
        "status",
        "created_at",
    )

    list_filter = ("status",)
    search_fields = ("user__username", "book__title")
    autocomplete_fields = ("user", "book")


@admin.register(BookGenre)
class BookGenreAdmin(admin.ModelAdmin):
    list_display = ("id", "book", "genre", "created_at")
    autocomplete_fields = ("book", "genre")
