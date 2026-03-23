import pytest
from books.models.genre import Genre


@pytest.mark.django_db
class TestGenreModelUnit:
    """Unit tests for Genre model."""

    def test_genre_str(self, genre_factory, fake_data):
        """Test the string representation of the genre."""
        name = fake_data.word()
        genre = genre_factory.build(name=name)
        assert str(genre) == name
