from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth import get_user_model

from books.models import Book, Genre, BookGenre, UserBook
from common.enums import UserRole, RequestStatus, BookStatus

User = get_user_model()


class Command(BaseCommand):
    help = "Seed initial books, genres and book-genre mappings"

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("Seeding books and genres...")

        genres_data = [
            {"name": "Fiction", "description": "Literary works based on imagination rather than fact, including novels and short stories."},
            {"name": "Non-Fiction", "description": "Factual writing about real events, people, and information."},
            {"name": "Science Fiction", "description": "Speculative fiction exploring futuristic concepts, technology, and space exploration."},
            {"name": "Fantasy", "description": "Fiction featuring magical elements, mythical creatures, and supernatural worlds."},
            {"name": "Mystery", "description": "Stories centered around solving crimes or uncovering secrets."},
            {"name": "Thriller", "description": "Fast-paced stories designed to create suspense and excitement."},
            {"name": "Romance", "description": "Stories focusing on romantic relationships and emotional connections."},
            {"name": "Horror", "description": "Fiction intended to frighten, scare, or create feelings of dread."},
            {"name": "Biography", "description": "Non-fiction accounts of a person's life written by someone else."},
            {"name": "History", "description": "Works documenting and analyzing past events and civilizations."},
            {"name": "Self-Help", "description": "Books offering guidance for personal improvement and well-being."},
            {"name": "Technology", "description": "Books about computing, software, hardware, and technological innovations."},
            {"name": "Machine Learning", "description": "Technical books about AI algorithms that learn from data."},
            {"name": "Data Science", "description": "Books covering data analysis, statistics, and extracting insights from data."},
            {"name": "Deep Learning", "description": "Advanced AI books focusing on neural networks and deep learning architectures."},
        ]

        genres = {}
        for data in genres_data:
            genre, created = Genre.objects.update_or_create(
                name=data["name"],
                defaults={"description": data["description"]},
            )
            genres[genre.name] = genre
            if created:
                self.stdout.write(f"  Created genre: {genre.name}")
            else:
                self.stdout.write(f"  Genre exists: {genre.name}")

        books_data = [
            {
                "title": "Deep Learning",
                "isbn": "9780262035613",
                "author": "Ian Goodfellow",
                "published_year": 2016,
                "genres": ["Technology", "Machine Learning", "Deep Learning"],
            },
            {
                "title": "Pattern Recognition and Machine Learning",
                "isbn": "9780387310732",
                "author": "Christopher Bishop",
                "published_year": 2006,
                "genres": ["Technology", "Machine Learning"],
            },
            {
                "title": "Hands-On Machine Learning",
                "isbn": "9781492032649",
                "author": "Aurelien Geron",
                "published_year": 2019,
                "genres": ["Technology", "Machine Learning", "Data Science"],
            },
            {
                "title": "The Great Gatsby",
                "isbn": "9780743273565",
                "author": "F. Scott Fitzgerald",
                "published_year": 1925,
                "genres": ["Fiction", "Romance"],
            },
            {
                "title": "To Kill a Mockingbird",
                "isbn": "9780061120084",
                "author": "Harper Lee",
                "published_year": 1960,
                "genres": ["Fiction", "History"],
            },
            {
                "title": "1984",
                "isbn": "9780451524935",
                "author": "George Orwell",
                "published_year": 1949,
                "genres": ["Fiction", "Science Fiction", "Thriller"],
            },
            {
                "title": "The Shining",
                "isbn": "9780307743657",
                "author": "Stephen King",
                "published_year": 1977,
                "genres": ["Fiction", "Horror", "Thriller"],
            },
            {
                "title": "Steve Jobs",
                "isbn": "9781451648539",
                "author": "Walter Isaacson",
                "published_year": 2011,
                "genres": ["Non-Fiction", "Biography", "Technology"],
            },
        ]

        user = User.objects.filter(role=UserRole.ADMIN).first()

        for data in books_data:
            book, created = Book.objects.get_or_create(
                isbn=data["isbn"],
                defaults={
                    "title": data["title"],
                    "author": data["author"],
                    "published_year": data["published_year"],
                    "request_status": RequestStatus.APPROVED,
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

            if user:

                UserBook.objects.get_or_create(
                    user=user,
                    book=book,
                    defaults={"status": BookStatus.TO_READ},
                )

        self.stdout.write(self.style.SUCCESS("\nSeeding completed successfully!"))
        self.stdout.write(f"  Total genres: {Genre.objects.count()}")
        self.stdout.write(f"  Total books: {Book.objects.count()}")
