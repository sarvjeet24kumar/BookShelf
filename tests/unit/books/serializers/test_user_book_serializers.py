import pytest
from books.serializers.user_book_serializers import UserBookAddSerializer, UserBookUpdateSerializer
from common.enums import BookStatus

class TestUserBookSerializersUnit:
    """Unit tests for UserBook serializers."""

    def test_user_book_add_invalid_status(self, fake_data):
        """Test that invalid status raises ValidationError in UserBookAddSerializer."""
        data = {"book_id": str(fake_data.uuid4()), "status": "INVALID"}
        serializer = UserBookAddSerializer(data=data)
        assert not serializer.is_valid()
        assert "status" in serializer.errors

    def test_user_book_update_valid_status(self):
        """Test that valid status passes in UserBookUpdateSerializer."""
        data = {"status": BookStatus.COMPLETED}
        serializer = UserBookUpdateSerializer(data=data)
        assert serializer.is_valid()
