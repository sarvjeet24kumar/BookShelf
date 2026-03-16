import pytest
from books.models.book import Book

@pytest.mark.django_db
class TestBookModelUnit:
    """Unit tests for Book model."""

    def test_book_str(self, book_factory, fake_data):
        """Test the string representation of the book."""
        title = fake_data.sentence(nb_words=3)
        author = fake_data.name()
        book = book_factory.build(title=title, author=author)
        assert str(book) == f"{title} by {author}"
