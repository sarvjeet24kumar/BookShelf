import pytest
from unittest.mock import MagicMock
from books.serializers.book_serializers import (
    BookCreateSerializer,
    BookUpdateSerializer,
)
from common.enums import RequestStatus, UserRole
from rest_framework import serializers


@pytest.mark.django_db
class TestBookCreateSerializerUnit:
    """Unit tests for BookCreateSerializer validation."""

    def test_validate_genres_empty(self):
        """Test that empty genres raise ValidationError."""
        serializer = BookCreateSerializer(data={"genres": []})
        assert not serializer.is_valid()
        assert "At least one genre is required" in str(
            serializer.errors.get("genres", [])
        )

    def test_validate_genres_non_existent(self, db, fake_data):
        """Test that non-existent genre IDs raise ValidationError."""
        non_existent_id = fake_data.uuid4()
        serializer = BookCreateSerializer(data={"genres": [non_existent_id]})
        assert not serializer.is_valid()
        error_str = str(serializer.errors.get("genres", []))
        assert (
            "IDs not found" in error_str
            or "None of the provided genre IDs exist" in error_str
        )

    def test_validate_isbn_duplicate(self, book_factory, fake_data):
        """Test that duplicate ISBN raises ValidationError."""
        isbn = fake_data.isbn13(separator="")
        book_factory(isbn=isbn)
        serializer = BookCreateSerializer(data={"isbn": isbn})
        assert not serializer.is_valid()
        assert "ISBN already exists" in str(serializer.errors.get("isbn", []))


class TestBookUpdateSerializerUnit:
    """Unit tests for BookUpdateSerializer validation."""

    def test_non_admin_cannot_change_status(self):
        """Test that non-admin users cannot change request_status."""
        mock_user = MagicMock(role=UserRole.USER)
        mock_request = MagicMock(user=mock_user)

        data = {"request_status": RequestStatus.APPROVED}
        serializer = BookUpdateSerializer(
            data=data, context={"request": mock_request}, partial=True
        )
        assert not serializer.is_valid()
        assert "Only admins can change the request status" in str(
            serializer.errors.get("request_status", [])
        )
