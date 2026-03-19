"""Unit tests for UserBooksView and UserBookDetailView ."""

import pytest
import uuid
from unittest.mock import patch, MagicMock
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework.exceptions import NotFound
from books.models import Book as RealBook
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
    """Unit tests for UserBooksView.get() and .post()."""

    @patch("books.views.user_book_views.CommonPagination")
    @patch("books.views.user_book_views.MyBookFilter")
    @patch("books.views.user_book_views.Book")
    def test_get_user_books(
        self, MockBook, MockFilter, MockPaginator, list_view, factory, mock_user
    ):
        """List user books should return paginated response."""
        mock_qs = MagicMock()
        MockBook.objects.filter.return_value.select_related.return_value.prefetch_related.return_value = (
            mock_qs
        )
        MockFilter.return_value.qs = mock_qs

        mock_paginator_instance = MockPaginator.return_value
        mock_paginator_instance.paginate_queryset.return_value = []
        mock_paginator_instance.get_paginated_response.return_value = Response(
            {"data": []}
        )

        request = factory.get(f"/api/v1/users/{mock_user.id}/books/")
        force_authenticate(request, user=mock_user)

        with patch.object(UserBooksView, "check_permission", return_value=mock_user):
            with patch("books.views.user_book_views.UserBookListSerializer") as MockSer:
                MockSer.return_value.data = []
                response = list_view(request, user_id=mock_user.id)
                assert response.status_code == status.HTTP_200_OK

    @patch("books.views.user_book_views.UserBook")
    @patch("books.views.user_book_views.Book")
    def test_add_book_not_found(
        self, MockBook, MockUserBook, list_view, factory, mock_user, fake_data
    ):
        """Non-existent book should return 404."""

        MockBook.DoesNotExist = RealBook.DoesNotExist
        MockBook.objects.get.side_effect = RealBook.DoesNotExist

        with patch.object(UserBooksView, "check_permission", return_value=mock_user):
            with patch("books.views.user_book_views.UserBookAddSerializer") as MockSer:
                mock_ser = MockSer.return_value
                mock_ser.is_valid.return_value = True
                book_id = str(uuid.uuid4())
                mock_ser.validated_data = {
                    "book_id": book_id,
                    "status": BookStatus.READING,
                }

                request = factory.post(
                    f"/api/v1/users/{mock_user.id}/books/",
                    {"book_id": book_id, "status": BookStatus.READING},
                )
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

        request = factory.post(
            f"/api/v1/users/{mock_user.id}/books/",
            {"book_id": str(uuid.uuid4()), "status": BookStatus.READING},
        )
        force_authenticate(request, user=mock_user)
        response = list_view(request, user_id=mock_user.id)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Only APPROVED books can be added" in str(
            response.data["error"]["details"]
        )

    @patch("books.views.user_book_views.UserBook")
    @patch("books.views.user_book_views.Book")
    def test_add_existing_book(
        self, MockBook, MockUserBook, list_view, factory, mock_user
    ):
        """Adding a book already in library should return 400."""
        mock_book = MagicMock()
        mock_book.request_status = RequestStatus.APPROVED
        MockBook.objects.get.return_value = mock_book

        mock_user_book = MagicMock()
        mock_user_book.deleted_at = None
        MockUserBook.all_objects.filter.return_value.first.return_value = mock_user_book

        request = factory.post(
            f"/api/v1/users/{mock_user.id}/books/",
            {"book_id": str(uuid.uuid4()), "status": BookStatus.READING},
        )
        force_authenticate(request, user=mock_user)
        response = list_view(request, user_id=mock_user.id)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Book already in library." in str(response.data["error"]["details"])

    @patch("books.views.user_book_views.UserBook")
    @patch("books.views.user_book_views.Book")
    def test_add_book_success(
        self, MockBook, MockUserBook, list_view, factory, mock_user, fake_data
    ):
        """Adding an approved book should return 201."""
        mock_book = MagicMock()
        mock_book.request_status = RequestStatus.APPROVED
        MockBook.objects.get.return_value = mock_book

        MockUserBook.all_objects.filter.return_value.first.return_value = None

        mock_user.tenant = MagicMock()
        mock_user.tenant.subscription_plan = SubscriptionPlan.PREMIUM

        with patch.object(UserBooksView, "check_permission", return_value=mock_user):
            with patch("books.views.user_book_views.UserBookAddSerializer") as MockSer:
                mock_ser = MockSer.return_value
                mock_ser.is_valid.return_value = True
                book_id = str(fake_data.uuid4())
                mock_ser.validated_data = {
                    "book_id": book_id,
                    "status": BookStatus.READING,
                }

                request = factory.post(
                    f"/api/v1/users/{mock_user.id}/books/",
                    {"book_id": book_id, "status": BookStatus.READING},
                )
                force_authenticate(request, user=mock_user)
                response = list_view(request, user_id=mock_user.id)
                assert response.status_code == status.HTTP_201_CREATED

    @patch("books.views.user_book_views.UserBook")
    @patch("books.views.user_book_views.Book")
    def test_add_book_free_plan_limit_reached(
        self, MockBook, MockUserBook, list_view, factory, mock_user, fake_data
    ):
        """Free plan user exceeding book limit should return 400."""
        mock_book = MagicMock()
        mock_book.request_status = RequestStatus.APPROVED
        MockBook.objects.get.return_value = mock_book

        MockUserBook.all_objects.filter.return_value.first.return_value = None
        MockUserBook.objects.filter.return_value.count.return_value = 100
        mock_user.tenant = MagicMock()
        mock_user.tenant.subscription_plan = SubscriptionPlan.FREE

        with patch.object(UserBooksView, "check_permission", return_value=mock_user):
            with patch("books.views.user_book_views.UserBookAddSerializer") as MockSer:
                mock_ser = MockSer.return_value
                mock_ser.is_valid.return_value = True
                book_id = str(fake_data.uuid4())
                mock_ser.validated_data = {
                    "book_id": book_id,
                    "status": BookStatus.READING,
                }

                request = factory.post(
                    f"/api/v1/users/{mock_user.id}/books/",
                    {"book_id": book_id, "status": BookStatus.READING},
                )
                force_authenticate(request, user=mock_user)
                response = list_view(request, user_id=mock_user.id)
                assert response.status_code == status.HTTP_400_BAD_REQUEST
                assert "plan limit reached" in str(response.data["error"]["details"])

    @patch("books.views.user_book_views.UserBook")
    @patch("books.views.user_book_views.Book")
    def test_add_book_restore_deleted_free_limit(
        self, MockBook, MockUserBook, list_view, factory, mock_user, fake_data
    ):
        """Restoring a deleted book should check free plan limit and then succeed."""
        mock_book = MagicMock()
        mock_book.request_status = RequestStatus.APPROVED
        MockBook.objects.get.return_value = mock_book

        mock_user_book = MagicMock()
        mock_user_book.deleted_at = "2025-05-21"
        MockUserBook.all_objects.filter.return_value.first.return_value = mock_user_book
        MockUserBook.objects.filter.return_value.count.return_value = 1

        mock_user.tenant = MagicMock()
        mock_user.tenant.subscription_plan = SubscriptionPlan.FREE

        with patch.object(UserBooksView, "check_permission", return_value=mock_user):
            with patch("books.views.user_book_views.UserBookAddSerializer") as MockSer:
                mock_ser = MockSer.return_value
                mock_ser.is_valid.return_value = True
                mock_ser.validated_data = {
                    "book_id": str(fake_data.uuid4()),
                    "status": BookStatus.READING,
                }

                request = factory.post(
                    f"/api/v1/users/{mock_user.id}/books/",
                    {"book_id": "1", "status": BookStatus.READING},
                )
                force_authenticate(request, user=mock_user)
                response = list_view(request, user_id=mock_user.id)
                assert response.status_code == status.HTTP_201_CREATED
                mock_user_book.restore.assert_called_once()


class TestUserBookDetailView:
    """Unit tests for UserBookDetailView."""

    def test_delete_book_from_library(self, detail_view, factory, mock_user, fake_data):
        """Removing book from library should soft delete and return 204."""
        mock_user_book = MagicMock()
        mock_user_book.soft_delete = MagicMock()

        book_id = str(fake_data.random_int())
        with patch.object(
            UserBookDetailView,
            "get_user_book",
            return_value=(mock_user_book, mock_user),
        ):
            request = factory.delete(f"/api/v1/users/{mock_user.id}/books/{book_id}/")
            force_authenticate(request, user=mock_user)
            response = detail_view(request, user_id=mock_user.id, book_id=book_id)
            assert response.status_code == status.HTTP_204_NO_CONTENT
            mock_user_book.soft_delete.assert_called_once()

    @patch("books.views.user_book_views.UserBook")
    def test_get_user_book_success(
        self, MockUserBook, detail_view, factory, mock_user, fake_data
    ):
        """get_user_book returns user_book and target_user."""
        mock_user_book = MagicMock()
        MockUserBook.objects.filter.return_value.first.return_value = mock_user_book
        mock_user_book.deleted_at = None

        book_id = str(fake_data.random_int())
        request = factory.get(f"/api/v1/users/{mock_user.id}/books/{book_id}/")
        force_authenticate(request, user=mock_user)

        view = UserBookDetailView()
        with patch.object(
            UserBookDetailView, "check_permission", return_value=mock_user
        ):
            obj, u = view.get_user_book(request, mock_user.id, book_id)
            assert obj == mock_user_book
            assert u == mock_user

    @patch("books.views.user_book_views.UserBook")
    def test_get_user_book_not_found(
        self, MockUserBook, detail_view, factory, mock_user, fake_data
    ):
        """get_user_book raises NotFound when book isn't in library."""
        MockUserBook.objects.filter.return_value.first.return_value = None

        book_id = str(fake_data.random_int())
        request = factory.get(f"/api/v1/users/{mock_user.id}/books/{book_id}/")
        force_authenticate(request, user=mock_user)

        view = UserBookDetailView()
        with patch.object(
            UserBookDetailView, "check_permission", return_value=mock_user
        ):
            with pytest.raises(NotFound):
                view.get_user_book(request, mock_user.id, book_id)

    @patch("books.views.user_book_views.Book")
    def test_get_book_from_library(
        self, MockBook, detail_view, factory, mock_user, fake_data
    ):
        """GET specific book in library."""
        mock_book = MagicMock()
        MockBook.objects.filter.return_value.select_related.return_value.prefetch_related.return_value.first.return_value = (
            mock_book
        )

        book_id = str(fake_data.random_int())
        with patch.object(
            UserBookDetailView, "check_permission", return_value=mock_user
        ):
            with patch("books.views.user_book_views.UserBookListSerializer") as MockSer:
                MockSer.return_value.data = {"status": "READING"}

                request = factory.get(f"/api/v1/users/{mock_user.id}/books/{book_id}/")
                force_authenticate(request, user=mock_user)
                response = detail_view(request, user_id=mock_user.id, book_id=book_id)
                assert response.status_code == status.HTTP_200_OK

    def test_patch_book_status(self, detail_view, factory, mock_user, fake_data):
        """PATCH reading status of book in library."""
        mock_user_book = MagicMock()

        book_id = str(fake_data.random_int())
        with patch.object(
            UserBookDetailView,
            "get_user_book",
            return_value=(mock_user_book, mock_user),
        ):
            with patch(
                "books.views.user_book_views.UserBookUpdateSerializer"
            ) as MockSer:
                mock_ser = MockSer.return_value
                mock_ser.is_valid.return_value = True
                mock_ser.validated_data = {"status": BookStatus.COMPLETED}

                request = factory.patch(
                    f"/api/v1/users/{mock_user.id}/books/{book_id}/",
                    {"status": BookStatus.COMPLETED},
                )
                force_authenticate(request, user=mock_user)
                response = detail_view(request, user_id=mock_user.id, book_id=book_id)
                assert response.status_code == status.HTTP_200_OK
                mock_user_book.save.assert_called_once()
