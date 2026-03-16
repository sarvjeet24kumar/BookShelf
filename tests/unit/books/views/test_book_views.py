"""Unit tests for BookView and BookDetailView — all dependencies mocked."""

import pytest
import uuid
from unittest.mock import patch, MagicMock
from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework.exceptions import ValidationError
from books.models import Book as RealBook
from books.views.book_views import BookView, BookDetailView
from common.enums import UserRole, RequestStatus


@pytest.fixture
def list_view():
    return BookView.as_view()


@pytest.fixture
def detail_view():
    return BookDetailView.as_view()


@pytest.fixture
def factory():
    return APIRequestFactory()


class TestBookViewGet:
    """Unit tests for BookView.get() — list books."""

    @patch("books.views.book_views.BookListSerializer")
    @patch("books.views.book_views.BookFilter")
    @patch("books.views.book_views.book_cache_service")
    @patch("books.views.book_views.Book")
    def test_list_books_admin_cache_miss(
        self,
        MockBook,
        mock_cache_svc,
        MockFilter,
        MockSerializer,
        list_view,
        factory,
        mock_admin,
    ):
        """Admin with cache miss should query all_objects and populate cache."""
        mock_cache_svc.get_books_for_tenant.return_value = None
        mock_qs = MagicMock()
        mock_qs.distinct.return_value.select_related.return_value.prefetch_related.return_value = (
            []
        )
        MockBook.all_objects.filter.return_value = mock_qs
        MockFilter.return_value.qs = mock_qs

        mock_ser = MockSerializer.return_value
        mock_ser.data = []

        request = factory.get("/api/v1/books/")
        force_authenticate(request, user=mock_admin)
        response = list_view(request)
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, dict)  # Adjusted for paginated response
        assert response.data["data"] == []  # Adjusted for paginated response
        mock_cache_svc.get_books_for_tenant.assert_called_once()

    @patch("books.views.book_views.BookListSerializer")
    @patch("books.views.book_views.book_cache_service")
    def test_list_books_cache_hit(
        self, mock_cache_svc, MockSerializer, list_view, factory, mock_user, fake_data
    ):
        """Cache hit should return cached data without DB query."""
        cached_data = [
            {"id": str(fake_data.uuid4()), "title": fake_data.sentence(nb_words=3)}
        ]
        mock_cache_svc.get_books_for_tenant.return_value = cached_data

        request = factory.get("/api/v1/books/")
        force_authenticate(request, user=mock_user)
        response = list_view(request)
        assert response.status_code == status.HTTP_200_OK
        # The view paginates cached data, so it should be in "data"
        assert response.data["data"] == cached_data
        mock_cache_svc.get_books_for_tenant.assert_called_once()


class TestBookViewPost:
    """Unit tests for BookView.post() — create book."""

    @patch("books.views.book_views.BookListSerializer")
    @patch("books.views.book_views.BookCreateSerializer")
    def test_create_book_success(
        self,
        MockCreateSerializer,
        MockListSerializer,
        list_view,
        factory,
        mock_user,
        fake_data,
    ):
        """Valid book data should create book and return 201."""
        mock_ser = MockCreateSerializer.return_value
        mock_ser.is_valid.return_value = True
        mock_book = MagicMock()
        mock_ser.save.return_value = mock_book

        book_title = fake_data.sentence(nb_words=3)
        mock_id = str(fake_data.uuid4())
        mock_list_ser = MockListSerializer.return_value
        mock_list_ser.data = {"id": mock_id, "title": book_title}

        request = factory.post("/api/v1/books/", {})
        force_authenticate(request, user=mock_user)
        response = list_view(request)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["id"] == mock_id
        assert response.data["title"] == book_title

    @patch("books.views.book_views.BookCreateSerializer")
    def test_create_book_invalid_data(
        self, MockSerializer, list_view, factory, mock_user
    ):
        """Invalid book data should return 400."""

        mock_ser = MockSerializer.return_value
        mock_ser.is_valid.side_effect = ValidationError({"title": "Required."})

        request = factory.post("/api/v1/books/", {})
        force_authenticate(request, user=mock_user)
        response = list_view(request)
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestBookDetailView:
    """Unit tests for BookDetailView."""

    @patch("books.views.book_views.BookListSerializer")
    @patch("books.views.book_views.Book")
    def test_get_book_as_admin(
        self, MockBook, MockSerializer, detail_view, factory, mock_admin, fake_data
    ):
        """Admin should retrieve any book."""
        mock_book = MagicMock()
        mock_book.request_status = RequestStatus.APPROVED
        MockBook.all_objects.get.return_value = mock_book

        mock_ser = MockSerializer.return_value
        mock_data = {
            "id": str(fake_data.uuid4()),
            "title": fake_data.sentence(nb_words=3),
        }
        mock_ser.data = mock_data

        request = factory.get("/api/v1/books/1/")
        force_authenticate(request, user=mock_admin)
        response = detail_view(request, id="1")
        assert response.status_code == status.HTTP_200_OK
        assert response.data == mock_data

    @patch("books.views.book_views.Book")
    def test_get_book_not_found(self, MockBook, detail_view, factory, mock_admin):
        """Non-existent book should return 404."""

        MockBook.DoesNotExist = RealBook.DoesNotExist
        MockBook.all_objects.get.side_effect = RealBook.DoesNotExist

        request = factory.get("/api/v1/books/1/")
        force_authenticate(request, user=mock_admin)
        response = detail_view(request, id="1")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in str(response.data["error"]["message"]).lower()

    @patch("books.views.book_views.UserBook")
    @patch("books.views.book_views.Book")
    def test_delete_book_non_admin_blocked(
        self, MockBook, MockUserBook, detail_view, factory, mock_user
    ):
        """Non-admin user should get 403 when deleting."""
        request = factory.delete("/api/v1/books/1/")
        force_authenticate(request, user=mock_user)
        response = detail_view(request, id="1")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @patch("books.views.book_views.UserBook")
    @patch("books.views.book_views.Book")
    def test_delete_book_in_user_libraries_blocked(
        self, MockBook, MockUserBook, detail_view, factory, mock_admin
    ):
        """Book in user libraries should not be deleted — return 400."""
        mock_book = MagicMock()
        MockBook.all_objects.get.return_value = mock_book
        MockUserBook.objects.filter.return_value.exists.return_value = True

        request = factory.delete("/api/v1/books/1/")
        force_authenticate(request, user=mock_admin)
        response = detail_view(request, id="1")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @patch("books.views.book_views.UserBook")
    @patch("books.views.book_views.Book")
    def test_delete_book_success(
        self, MockBook, MockUserBook, detail_view, factory, mock_admin
    ):
        """Admin deleting book not in any library should return 204."""
        mock_book = MagicMock()
        MockBook.all_objects.get.return_value = mock_book
        MockUserBook.objects.filter.return_value.exists.return_value = False

        request = factory.delete("/api/v1/books/1/")
        force_authenticate(request, user=mock_admin)
        response = detail_view(request, id="1")
        assert response.status_code == status.HTTP_204_NO_CONTENT
        mock_book.soft_delete.assert_called_once()

    @patch("books.views.book_views.BookListSerializer")
    @patch("books.views.book_views.BookUpdateSerializer")
    @patch("books.views.book_views.Book")
    def test_patch_book_non_admin_non_owner_blocked(
        self,
        MockBook,
        MockUpdateSer,
        MockListSer,
        detail_view,
        factory,
        mock_user,
        fake_data,
    ):
        """Non-admin non-owner should get 403 on update."""
        mock_book = MagicMock()
        mock_book.created_by = MagicMock()  # different user
        mock_book.request_status = RequestStatus.APPROVED
        MockBook.objects.get.return_value = mock_book

        request = factory.patch(
            "/api/v1/books/1/", {"title": fake_data.sentence(nb_words=3)}, format="json"
        )
        force_authenticate(request, user=mock_user)
        response = detail_view(request, id="1")
        assert response.status_code == status.HTTP_403_FORBIDDEN
