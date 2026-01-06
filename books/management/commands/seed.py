from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth import get_user_model

from books.models import Book, Genre, BookGenre, UserBook


User = get_user_model()


class Command(BaseCommand):
    help = "Seed initial books, genres and book-genre mappings"

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("Seeding books and genres...")

        genres_data = [
            {"name": "ml"},
            {"name": "Machine Learning"},
            {"name": "Deep Learning"},
            {"name": "Data Science"},
        ]

        genres = {}
        for data in genres_data:
            genre, _ = Genre.objects.get_or_create(
                name=data["name"],
            
            )
            genres[genre.name] = genre

        books_data = [
            {
                "title": "Deep Learning",
                "isbn": "9780262035613",
                "author": "Ian Goodfellow",
                "published_year": 2013,
                "genres": ["ml", "Deep Learning"],
            },
            {
                "title": "Pattern Recognition and Machine Learning",
                "isbn": "9780387310732",
                "author": "Christopher Bishop",
                "published_year": 2012,
                "genres": ["Machine Learning"],
            },
            {
                "title": "Hands-On Machine Learning",
                "isbn": "9781492032649",
                "author": "Aurélien Géron",
                "published_year": 2012,
                "genres": ["Machine Learning", "Data Science"],
            },
        ]

        user = User.objects.first()

        for data in books_data:
            book, _ = Book.objects.get_or_create(
                isbn=data["isbn"],
                defaults={
                    "title": data["title"],
                    "author": data["author"],
                    "published_year": data["published_year"],
                },
            )

            for genre_name in data["genres"]:
                genre = genres.get(genre_name)
                if genre:
                    BookGenre.objects.get_or_create(
                        book=book,
                        genre=genre,
                    )
            if user:
                UserBook.objects.get_or_create(
                    user=user,
                    book=book,
                    defaults={"status": "TO_READ"},
                )

        self.stdout.write(self.style.SUCCESS("Seeding completed successfully"))
