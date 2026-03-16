"""Unit tests for UserBooksView and UserBookDetailView — all dependencies mocked."""
import pytest
import uuid
from unittest.mock import patch, MagicMock
from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate
from books.views.user_book_views import UserBooksView, UserBookDetailView
from common.enums import BookStatus, RequestStatus, SubscriptionPlan


@pytest.fixture
def list_view():
    return UserBooksView.as_view()


@pytest.fixture
def detail_view():
    return UserBookDetailView.as_view()


@pytest.fixture
def factory():
    return APIRequestFactory()


class TestUserBooksViewPost:
    """Unit tests for UserBooksView.post() — add book to library."""

    @patch("books.views.user_book_views.UserBook")
    @patch("books.views.user_book_views.Book")
    def test_add_book_not_found(self, MockBook, MockUserBook, list_view, factory, mock_user, fake_data):
        """Non-existent book should return 404."""
        from books.models import Book as RealBook
        MockBook.DoesNotExist = RealBook.DoesNotExist
        MockBook.objects.get.side_effect = RealBook.DoesNotExist

        with patch.object(UserBooksView, 'check_permission', return_value=mock_user):
            with patch("books.views.user_book_views.UserBookAddSerializer") as MockSer:
                mock_ser = MockSer.return_value
                mock_ser.is_valid.return_value = True
                book_id = str(uuid.uuid4())
                mock_ser.validated_data = {"book_id": book_id, "status": BookStatus.READING}

                request = factory.post(f"/api/v1/users/{mock_user.id}/books/", {"book_id": book_id, "status": BookStatus.READING})
                force_authenticate(request, user=mock_user)
            response = list_view(request, user_id=mock_user.id)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data["error"]["message"] == "Book not available or deleted."

    @patch("books.views.user_book_views.Book")
    def test_add_unapproved_book(self, MockBook, list_view, factory, mock_user):
        """Adding a non-approved book should return 400."""
        mock_book = MagicMock()
        mock_book.request_status = RequestStatus.PENDING
        MockBook.objects.get.return_value = mock_book

        request = factory.post(f"/api/v1/users/{mock_user.id}/books/", {"book_id": str(uuid.uuid4()), "status": BookStatus.READING})
        force_authenticate(request, user=mock_user)
        response = list_view(request, user_id=mock_user.id)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Only APPROVED books can be added" in str(response.data["error"]["details"])

    @patch("books.views.user_book_views.UserBook")
    @patch("books.views.user_book_views.Book")
    def test_add_existing_book(self, MockBook, MockUserBook, list_view, factory, mock_user):
        """Adding a book already in library should return 400."""
        mock_book = MagicMock()
        mock_book.request_status = RequestStatus.APPROVED
        MockBook.objects.get.return_value = mock_book

        mock_user_book = MagicMock()
        mock_user_book.deleted_at = None
        MockUserBook.all_objects.filter.return_value.first.return_value = mock_user_book

        request = factory.post(f"/api/v1/users/{mock_user.id}/books/", {"book_id": str(uuid.uuid4()), "status": BookStatus.READING})
        force_authenticate(request, user=mock_user)
        response = list_view(request, user_id=mock_user.id)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Book already in library." in str(response.data["error"]["details"])

    @patch("books.views.user_book_views.UserBook")
    @patch("books.views.user_book_views.Book")
    def test_add_book_success(self, MockBook, MockUserBook, list_view, factory, mock_user, fake_data):
        """Adding an approved book should return 201."""
        mock_book = MagicMock()
        mock_book.request_status = RequestStatus.APPROVED
        MockBook.objects.get.return_value = mock_book

        MockUserBook.all_objects.filter.return_value.first.return_value = None

        mock_user.tenant = MagicMock()
        mock_user.tenant.subscription_plan = SubscriptionPlan.PREMIUM

        with patch.object(UserBooksView, 'check_permission', return_value=mock_user):
            with patch("books.views.user_book_views.UserBookAddSerializer") as MockSer:
                mock_ser = MockSer.return_value
                mock_ser.is_valid.return_value = True
                book_id = str(fake_data.uuid4())
                mock_ser.validated_data = {"book_id": book_id, "status": BookStatus.READING}

                request = factory.post(f"/api/v1/users/{mock_user.id}/books/", {"book_id": book_id, "status": BookStatus.READING})
                force_authenticate(request, user=mock_user)
                response = list_view(request, user_id=mock_user.id)
                assert response.status_code == status.HTTP_201_CREATED

    @patch("books.views.user_book_views.UserBook")
    @patch("books.views.user_book_views.Book")
    def test_add_book_free_plan_limit_reached(self, MockBook, MockUserBook, list_view, factory, mock_user, fake_data):
        """Free plan user exceeding book limit should return 400."""
        mock_book = MagicMock()
        mock_book.request_status = RequestStatus.APPROVED
        MockBook.objects.get.return_value = mock_book

        MockUserBook.all_objects.filter.return_value.first.return_value = None
        MockUserBook.objects.filter.return_value.count.return_value = 100  # Over limit

        mock_user.tenant = MagicMock()
        mock_user.tenant.subscription_plan = SubscriptionPlan.FREE

        with patch.object(UserBooksView, 'check_permission', return_value=mock_user):
            with patch("books.views.user_book_views.UserBookAddSerializer") as MockSer:
                mock_ser = MockSer.return_value
                mock_ser.is_valid.return_value = True
                book_id = str(fake_data.uuid4())
                mock_ser.validated_data = {"book_id": book_id, "status": BookStatus.READING}

                request = factory.post(f"/api/v1/users/{mock_user.id}/books/", {"book_id": book_id, "status": BookStatus.READING})
                force_authenticate(request, user=mock_user)
                response = list_view(request, user_id=mock_user.id)
                assert response.status_code == status.HTTP_400_BAD_REQUEST
                assert "plan limit reached" in str(response.data["error"]["details"])


class TestUserBookDetailView:
    """Unit tests for UserBookDetailView."""

    def test_delete_book_from_library(self, detail_view, factory, mock_user):
        """Removing book from library should soft delete and return 204."""
        mock_user_book = MagicMock()
        mock_user_book.soft_delete = MagicMock()

        with patch.object(
            UserBookDetailView, 'get_object', return_value=(mock_user_book, mock_user)
        ):
            request = factory.delete(f"/api/v1/users/{mock_user.id}/books/1/")
            force_authenticate(request, user=mock_user)
            response = detail_view(request, user_id=mock_user.id, book_id="1")
            assert response.status_code == status.HTTP_204_NO_CONTENT
            mock_user_book.soft_delete.assert_called_once()
