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

        # At least 10 genres
        genres_data = [
            {"name": "Fiction"},
            {"name": "Non-Fiction"},
            {"name": "Science Fiction"},
            {"name": "Fantasy"},
            {"name": "Mystery"},
            {"name": "Thriller"},
            {"name": "Romance"},
            {"name": "Horror"},
            {"name": "Biography"},
            {"name": "History"},
            {"name": "Self-Help"},
            {"name": "Technology"},
            {"name": "Machine Learning"},
            {"name": "Data Science"},
            {"name": "Deep Learning"},
        ]

        genres = {}
        for data in genres_data:
            genre, created = Genre.objects.get_or_create(
                name=data["name"],
            )
            genres[genre.name] = genre
            if created:
                self.stdout.write(f"  Created genre: {genre.name}")
            else:
                self.stdout.write(f"  Genre exists: {genre.name}")

        # Sample books with genres
        books_data = [
            {
                "title": "Deep Learning",
                "isbn": "9780262035613",
                "author": "Ian Goodfellow",
                "published_year": 2016,
                "genres": ["Technology", "Machine Learning", "Deep Learning"],
                "request_status": "APPROVED",
            },
            {
                "title": "Pattern Recognition and Machine Learning",
                "isbn": "9780387310732",
                "author": "Christopher Bishop",
                "published_year": 2006,
                "genres": ["Technology", "Machine Learning"],
                "request_status": "APPROVED",
            },
            {
                "title": "Hands-On Machine Learning",
                "isbn": "9781492032649",
                "author": "Aurelien Geron",
                "published_year": 2019,
                "genres": ["Technology", "Machine Learning", "Data Science"],
                "request_status": "APPROVED",
            },
            {
                "title": "The Great Gatsby",
                "isbn": "9780743273565",
                "author": "F. Scott Fitzgerald",
                "published_year": 1925,
                "genres": ["Fiction", "Romance"],
                "request_status": "APPROVED",
            },
            {
                "title": "To Kill a Mockingbird",
                "isbn": "9780061120084",
                "author": "Harper Lee",
                "published_year": 1960,
                "genres": ["Fiction", "History"],
                "request_status": "APPROVED",
            },
            {
                "title": "1984",
                "isbn": "9780451524935",
                "author": "George Orwell",
                "published_year": 1949,
                "genres": ["Fiction", "Science Fiction", "Thriller"],
                "request_status": "PENDING",
            },
            {
                "title": "The Shining",
                "isbn": "9780307743657",
                "author": "Stephen King",
                "published_year": 1977,
                "genres": ["Fiction", "Horror", "Thriller"],
                "request_status": "APPROVED",
            },
            {
                "title": "Steve Jobs",
                "isbn": "9781451648539",
                "author": "Walter Isaacson",
                "published_year": 2011,
                "genres": ["Non-Fiction", "Biography", "Technology"],
                "request_status": "APPROVED",
            },
        ]

        user = User.objects.first()

        for data in books_data:
            book, created = Book.objects.get_or_create(
                isbn=data["isbn"],
                defaults={
                    "title": data["title"],
                    "author": data["author"],
                    "published_year": data["published_year"],
                    "request_status": data.get("request_status", "APPROVED"),
                    "created_by": user,
                },
            )
            
            if created:
                self.stdout.write(f"  Created book: {book.title}")
            else:
                self.stdout.write(f"  Book exists: {book.title}")

            for genre_name in data["genres"]:
                genre = genres.get(genre_name)
                if genre:
                    book_genre, bg_created = BookGenre.objects.get_or_create(
                        book=book,
                        genre=genre,
                    )
                    if bg_created:
                        self.stdout.write(f"    Linked to genre: {genre_name}")

            # Add to first user's reading list
            if user:
                UserBook.objects.get_or_create(
                    user=user,
                    book=book,
                    defaults={"status": "TO_READ"},
                )

        self.stdout.write(self.style.SUCCESS("\nSeeding completed successfully!"))
        self.stdout.write(f"  Total genres: {Genre.objects.count()}")
        self.stdout.write(f"  Total books: {Book.objects.count()}")
