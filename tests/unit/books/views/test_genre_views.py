"""Unit tests for GenreListView and GenreDetailView — all dependencies mocked."""

import pytest
from unittest.mock import patch, MagicMock
from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate
from books.views.genre_views import GenreListView, GenreDetailView
from common.enums import UserRole


@pytest.fixture
def list_view():
    return GenreListView.as_view()


@pytest.fixture
def detail_view():
    return GenreDetailView.as_view()


@pytest.fixture
def factory():
    return APIRequestFactory()


class TestGenreListView:
    """Unit tests for GenreListView."""

    @patch("books.views.genre_views.GenreSerializer")
    @patch("books.views.genre_views.Genre")
    def test_list_genres_as_admin(
        self, MockGenre, MockSerializer, list_view, factory, mock_admin
    ):
        """Admin should list all genres including soft-deleted."""
        mock_qs = MagicMock()
        mock_qs.order_by.return_value = []
        MockGenre.all_objects.all.return_value = mock_qs

        mock_ser = MockSerializer.return_value
        mock_ser.data = []

        request = factory.get("/api/v1/genres/")
        force_authenticate(request, user=mock_admin)
        response = list_view(request)
        assert response.status_code == status.HTTP_200_OK
        if isinstance(response.data, dict):
            assert "data" in response.data
            assert isinstance(response.data["data"], list)
        else:
            assert isinstance(response.data, list)

    @patch("books.views.genre_views.GenreSerializer")
    @patch("books.views.genre_views.Genre")
    def test_list_genres_as_non_admin(
        self, MockGenre, MockSerializer, list_view, factory, mock_user
    ):
        """Non-admin should list active genres."""
        mock_qs = MagicMock()
        mock_qs.order_by.return_value = []
        MockGenre.objects.all.return_value = mock_qs

        mock_ser = MockSerializer.return_value
        mock_ser.data = []

        request = factory.get("/api/v1/genres/")
        mock_user.role = UserRole.USER
        force_authenticate(request, user=mock_user)
        response = list_view(request)
        
        assert response.status_code == status.HTTP_200_OK
        MockGenre.objects.all.assert_called_once()
        assert MockSerializer.call_args[1].get('exclude_fields') == ['deleted_at']

    @patch("books.views.genre_views.GenreSerializer")
    def test_create_genre_non_admin_blocked(
        self, MockSerializer, list_view, factory, mock_user, fake_data
    ):
        """Non-admin user should get 403 when creating genre."""
        request = factory.post("/api/v1/genres/", {"name": fake_data.word()})
        force_authenticate(request, user=mock_user)
        response = list_view(request)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @patch("books.views.genre_views.GenreSerializer")
    def test_create_genre_admin_success(
        self, MockSerializer, list_view, factory, mock_admin, fake_data
    ):
        """Admin should create genre and return 201."""
        genre_name = fake_data.word()
        genre_id = str(fake_data.uuid4())
        mock_ser = MockSerializer.return_value
        mock_ser.is_valid.return_value = True
        mock_genre = MagicMock()
        mock_genre.id = genre_id
        mock_genre.name = genre_name
        mock_ser.save.return_value = mock_genre
        mock_ser.data = {"id": genre_id, "name": genre_name}

        request = factory.post("/api/v1/genres/", {"name": genre_name})
        force_authenticate(request, user=mock_admin)
        response = list_view(request)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["id"] == genre_id
        assert response.data["name"] == genre_name


class TestGenreDetailView:
    """Unit tests for GenreDetailView."""

    @patch("books.views.genre_views.Genre")
    def test_delete_genre_non_admin_blocked(
        self, MockGenre, detail_view, factory, mock_user
    ):
        """Non-admin user should get 403 when deleting genre."""
        request = factory.delete("/api/v1/genres/1/")
        force_authenticate(request, user=mock_user)
        response = detail_view(request, id="1")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @patch("books.views.genre_views.Genre")
    def test_update_genre_non_admin_blocked(
        self, MockGenre, detail_view, factory, mock_user, fake_data
    ):
        """Non-admin user should get 403 when updating genre."""
        request = factory.patch(
            "/api/v1/genres/1/", {"name": fake_data.word()}, format="json"
        )
        force_authenticate(request, user=mock_user)
        response = detail_view(request, id="1")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_genre_not_found(self, detail_view, factory, mock_admin):
        """Non-existent genre should return 404."""
        with patch(
            "books.views.genre_views.GenreDetailView.get_object", return_value=None
        ):
            request = factory.get("/api/v1/genres/1/")
            force_authenticate(request, user=mock_admin)
            response = detail_view(request, id="1")
            assert response.status_code == status.HTTP_404_NOT_FOUND
            assert response.data["error"]["message"] == "Genre not found."

    @patch("books.views.genre_views.Genre.all_objects.get")
    def test_get_genre_admin_success(self, mock_get, detail_view, factory, mock_admin, fake_data):
        """Admin should retrieve a genre successfully."""
        mock_genre = MagicMock()
        mock_genre.id = "1"
        mock_genre.name = fake_data.word()
        mock_get.return_value = mock_genre

        request = factory.get("/api/v1/genres/1/")
        force_authenticate(request, user=mock_admin)
        
        with patch("books.views.genre_views.GenreSerializer") as MockSer:
            mock_ser_instance = MockSer.return_value
            mock_ser_instance.data = {"id": mock_genre.id, "name": mock_genre.name}
            response = detail_view(request, id="1")
            
            assert response.status_code == status.HTTP_200_OK
            assert response.data["name"] == mock_genre.name
            MockSer.assert_called_once()
            assert MockSer.call_args[1].get('exclude_fields') == []

    @patch("books.views.genre_views.Genre.objects.get")
    def test_get_genre_non_admin_success(self, mock_get, detail_view, factory, mock_user, fake_data):
        """Non-admin should retrieve a genre successfully and exclude deleted_at."""
        mock_genre = MagicMock()
        mock_genre.id = "1"
        mock_genre.name = fake_data.word()
        mock_get.return_value = mock_genre

        request = factory.get("/api/v1/genres/1/")
        mock_user.role = UserRole.USER
        force_authenticate(request, user=mock_user)
        
        with patch("books.views.genre_views.GenreSerializer") as MockSer:
            mock_ser_instance = MockSer.return_value
            mock_ser_instance.data = {"id": mock_genre.id, "name": mock_genre.name}
            response = detail_view(request, id="1")
            
            assert response.status_code == status.HTTP_200_OK
            assert MockSer.call_args[1].get('exclude_fields') == ['deleted_at']

    @patch("books.views.genre_views.GenreDetailView.get_object")
    def test_patch_genre_admin_success(self, mock_get_object, detail_view, factory, mock_admin, fake_data):
        """Admin should update a genre successfully."""
        mock_genre = MagicMock()
        mock_genre.id = "1"
        mock_get_object.return_value = mock_genre

        request = factory.patch("/api/v1/genres/1/", {"name": "Updated"}, format="json")
        force_authenticate(request, user=mock_admin)
        
        with patch("books.views.genre_views.GenreSerializer") as MockSer:
            mock_ser_instance = MockSer.return_value
            mock_ser_instance.is_valid.return_value = True
            mock_ser_instance.data = {"id": "1", "name": "Updated"}
            response = detail_view(request, id="1")
            
            assert response.status_code == status.HTTP_200_OK
            mock_ser_instance.save.assert_called_once()

    @patch("books.views.genre_views.GenreDetailView.get_object", return_value=None)
    def test_patch_genre_admin_not_found(self, mock_get_object, detail_view, factory, mock_admin):
        """Admin updating non-existent genre returns 404."""
        request = factory.patch("/api/v1/genres/1/", {"name": "Updated"}, format="json")
        force_authenticate(request, user=mock_admin)
        response = detail_view(request, id="1")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @patch("books.views.genre_views.GenreDetailView.get_object")
    def test_delete_genre_admin_success(self, mock_get_object, detail_view, factory, mock_admin):
        """Admin should delete a genre successfully."""
        mock_genre = MagicMock()
        mock_genre.id = "1"
        mock_get_object.return_value = mock_genre

        request = factory.delete("/api/v1/genres/1/")
        force_authenticate(request, user=mock_admin)
        response = detail_view(request, id="1")
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        mock_genre.delete.assert_called_once()

    @patch("books.views.genre_views.GenreDetailView.get_object", return_value=None)
    def test_delete_genre_admin_not_found(self, mock_get_object, detail_view, factory, mock_admin):
        """Admin deleting non-existent genre returns 404."""
        request = factory.delete("/api/v1/genres/1/")
        force_authenticate(request, user=mock_admin)
        response = detail_view(request, id="1")
        assert response.status_code == status.HTTP_404_NOT_FOUND


