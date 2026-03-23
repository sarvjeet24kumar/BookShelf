import pytest
from books.serializers.genre_serializers import GenreSerializer
from unittest.mock import MagicMock


@pytest.mark.django_db
class TestGenreSerializerUnit:
    """Unit tests for GenreSerializer validation."""

    def test_duplicate_genre_name_fails(self, genre_factory, user, fake_data):
        """Test that duplicate genre name for the same tenant fails."""
        genre_name = fake_data.word()
        genre_factory(name=genre_name, tenant=user.tenant)

        mock_request = MagicMock(user=user)
        data = {"name": f"  {genre_name.upper()}  "}
        serializer = GenreSerializer(data=data, context={"request": mock_request})

        assert not serializer.is_valid()
        assert "A genre with this name already exists" in str(
            serializer.errors.get("name", [])
        )
