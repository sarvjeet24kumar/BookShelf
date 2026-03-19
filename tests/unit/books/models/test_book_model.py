import pytest
from django.db import IntegrityError
from common.enums import RequestStatus
from books.models.book import Book


@pytest.mark.django_db
class TestBookModelUnit:
    """Unit tests for Book model."""

    def test_book_creation(self, book_factory, tenant, fake_data):
        """Book is created with correct field values."""
        title = fake_data.sentence(nb_words=3)
        author = fake_data.name()
        isbn = fake_data.isbn13(separator="")
        year = int(fake_data.year())
        book = book_factory.create(
            title=title,
            author=author,
            isbn=isbn,
            published_year=year,
            tenant=tenant,
        )
        assert book.title == title
        assert book.author == author
        assert book.isbn == isbn
        assert book.published_year == int(year)
        assert book.tenant == tenant

    def test_isbn_tenant_uniqueness(self, book_factory, tenant, fake_data):
        """Duplicate ISBNs within the same tenant raise an IntegrityError."""

        isbn = fake_data.isbn13(separator="")
        book_factory.create(isbn=isbn, tenant=tenant)
        with pytest.raises(IntegrityError):
            book_factory.create(isbn=isbn, tenant=tenant)

