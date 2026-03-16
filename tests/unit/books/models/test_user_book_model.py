import pytest
from books.models.user_book import UserBook
from common.enums import BookStatus


@pytest.mark.django_db
class TestUserBookModelUnit:
    """Unit tests for UserBook model."""

    def test_user_book_str(self, user_book_factory):
        """Test the string representation of the UserBook relationship."""
        # Use create to ensure related objects (user, book) are fully loaded for __str__
        user_book = user_book_factory.create(status=BookStatus.READING)
        expected_str = (
            f"{user_book.user} → {user_book.book.title} ({BookStatus.READING})"
        )
        assert str(user_book) == expected_str
