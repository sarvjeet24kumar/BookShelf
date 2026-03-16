"""Unit tests for UserView and UserDetailView — all dependencies mocked."""
import pytest
import uuid
from unittest.mock import patch, MagicMock
from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate
from accounts.views.user_views import UserView, UserDetailView
from common.enums import UserRole
from common.enums import UserRole


@pytest.fixture
def list_view():
    return UserView.as_view()


@pytest.fixture
def detail_view():
    return UserDetailView.as_view()


@pytest.fixture
def factory():
    return APIRequestFactory()


class TestUserViewList:
    """Unit tests for UserView GET (list users)."""

    @patch("accounts.views.user_views.User")
    def test_list_users_as_admin(self, MockUser, list_view, factory, mock_admin):
        """Admin should get 200 listing users."""
        mock_qs = MagicMock()
        mock_qs.order_by.return_value = []
        MockUser.objects.filter.return_value = mock_qs

        request = factory.get("/api/v1/users/")
        force_authenticate(request, user=mock_admin)
        response = list_view(request)
        assert response.status_code == status.HTTP_200_OK
        assert "data" in response.data or isinstance(response.data, list)
        MockUser.objects.filter.assert_called_once()

    @patch("accounts.views.user_views.User")
    def test_list_users_as_superadmin(self, MockUser, list_view, factory, mock_super_admin):
        """Super admin should get 200 listing admin users."""
        mock_qs = MagicMock()
        mock_qs.order_by.return_value = []
        MockUser.all_objects.filter.return_value = mock_qs

        request = factory.get("/api/v1/users/")
        force_authenticate(request, user=mock_super_admin)
        response = list_view(request)
        assert response.status_code == status.HTTP_200_OK
        MockUser.all_objects.filter.assert_called_once()


class TestUserViewCreate:
    """Unit tests for UserView POST (create user)."""

    @patch("accounts.views.user_views.email_verification_service")
    @patch("accounts.views.user_views.User")
    def test_create_user_as_admin_success(
        self, MockUser, mock_email_svc, list_view, factory, mock_admin, fake_data
    ):
        """Admin creating a user should return 200 and send verification email."""
        MockUser.all_objects.filter.return_value.exists.return_value = False

        mock_saved_user = MagicMock()
        mock_saved_user.username = fake_data.user_name()
        mock_saved_user.email = fake_data.email()

        request = factory.post("/api/v1/users/", {
            "username": fake_data.user_name(),
            "email": fake_data.email(),
            "password": fake_data.password(special_chars=True),
        })
        force_authenticate(request, user=mock_admin)

        with patch.object(UserView, 'get_serializer') as mock_get_ser:
            mock_ser = MagicMock()
            mock_ser.is_valid.return_value = True
            mock_ser.validated_data = {"email": fake_data.email()}
            mock_ser.save.return_value = mock_saved_user
            mock_get_ser.return_value = mock_ser

            response = list_view(request)
            assert response.status_code == status.HTTP_200_OK
            assert "Verification code sent to your email." in response.data["detail"]
            mock_email_svc.create.assert_called_once()

    @patch("accounts.views.user_views.User")
    def test_create_user_duplicate_email(self, MockUser, list_view, factory, mock_admin, fake_data):
        """Duplicate email should return 400."""
        MockUser.all_objects.filter.return_value.exists.return_value = True

        dup_email = fake_data.email()
        request = factory.post("/api/v1/users/", {
            "username": fake_data.user_name(),
            "email": dup_email,
            "password": fake_data.password(special_chars=True),
        })
        force_authenticate(request, user=mock_admin)

        with patch.object(UserView, 'get_serializer') as mock_get_ser:
            mock_ser = MagicMock()
            mock_ser.is_valid.return_value = True
            mock_ser.validated_data = {"email": dup_email}
            mock_get_ser.return_value = mock_ser

            response = list_view(request)
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert "A user with this email already exists." in str(response.data["error"]["details"])

    @patch("accounts.views.user_views.User")
    def test_create_admin_as_superadmin_requires_tenant(
        self, MockUser, list_view, factory, mock_super_admin, fake_data
    ):
        """Super admin creating admin without tenant should return 400."""
        new_email = fake_data.email()
        request = factory.post("/api/v1/users/", {
            "username": fake_data.user_name(),
            "email": new_email,
            "password": fake_data.password(special_chars=True),
        })
        force_authenticate(request, user=mock_super_admin)

        with patch.object(UserView, 'get_serializer') as mock_get_ser:
            mock_ser = MagicMock()
            mock_ser.is_valid.return_value = True
            mock_ser.validated_data = {"email": new_email, "tenant": None}
            mock_get_ser.return_value = mock_ser

            response = list_view(request)
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert "Tenant" in str(response.data["error"]["details"])


class TestUserDetailViewUpdate:
    """Unit tests for UserDetailView PUT (update user)."""

    def test_update_email_blocked(self, detail_view, factory, mock_user, mock_admin, fake_data):
        """Attempting to update email should return 403."""
        request = factory.put(
            f"/api/v1/users/{mock_user.id}/",
            {"email": fake_data.email()},
            format="json"
        )
        force_authenticate(request, user=mock_admin)

        with patch.object(UserDetailView, 'get_object', return_value=mock_user):
            response = detail_view(request, id=mock_user.id)
            assert response.status_code == status.HTTP_403_FORBIDDEN
            assert "Email and role cannot be changed." in str(response.data["error"]["message"])

    def test_update_role_blocked(self, detail_view, factory, mock_user, mock_admin):
        """Attempting to update role should return 403."""
        request = factory.put(
            f"/api/v1/users/{mock_user.id}/",
            {"role": "admin"},
            format="json"
        )
        force_authenticate(request, user=mock_admin)

        with patch.object(UserDetailView, 'get_object', return_value=mock_user):
            response = detail_view(request, id=mock_user.id)
            assert response.status_code == status.HTTP_403_FORBIDDEN
            assert "Email and role cannot be changed." in str(response.data["error"]["message"])

    def test_regular_user_cannot_update_restricted_fields(
        self, detail_view, factory, mock_user
    ):
        """Regular user cannot update is_active — should return 403."""
        request = factory.put(
            f"/api/v1/users/{mock_user.id}/",
            {"is_active": False},
            format="json"
        )
        mock_user.role = UserRole.USER
        force_authenticate(request, user=mock_user)

        with patch.object(UserDetailView, 'get_object', return_value=mock_user):
            response = detail_view(request, id=mock_user.id)
            assert response.status_code == status.HTTP_403_FORBIDDEN
            assert "You cannot update restricted fields (is_active, deleted_at)." in str(response.data["error"]["message"])


class TestUserDetailViewDestroy:
    """Unit tests for UserDetailView DELETE."""

    @patch("accounts.views.user_views.blacklist_user_tokens")
    def test_admin_cannot_delete_self(self, mock_blacklist, detail_view, factory, mock_admin):
        """Admin deleting themselves should return 403."""
        request = factory.delete(f"/api/v1/users/{mock_admin.id}/")
        force_authenticate(request, user=mock_admin)

        with patch.object(UserDetailView, 'get_object', return_value=mock_admin):
            response = detail_view(request, id=mock_admin.id)
            assert response.status_code == status.HTTP_403_FORBIDDEN
            assert "Admins cannot delete their own account." in str(response.data["error"]["message"])

    @patch("accounts.views.user_views.transaction")
    @patch("accounts.views.user_views.blacklist_user_tokens")
    def test_admin_delete_user_success(
        self, mock_blacklist, mock_transaction, detail_view, factory, mock_admin, mock_user
    ):
        """Admin deleting a regular user should return 204."""
        mock_transaction.atomic.return_value.__enter__ = MagicMock()
        mock_transaction.atomic.return_value.__exit__ = MagicMock(return_value=False)

        request = factory.delete(f"/api/v1/users/{mock_user.id}/")
        force_authenticate(request, user=mock_admin)

        with patch.object(UserDetailView, 'get_object', return_value=mock_user):
            response = detail_view(request, id=mock_user.id)
            assert response.status_code == status.HTTP_204_NO_CONTENT
            mock_user.soft_delete.assert_called_once()
            mock_blacklist.assert_called_once_with(mock_user)

    @patch("accounts.views.user_views.blacklist_user_tokens")
    def test_admin_cannot_delete_other_admin(
        self, mock_blacklist, detail_view, factory, mock_admin
    ):
        """Tenant admin cannot delete another admin — should return 403."""
        other_admin = MagicMock()
        other_admin.id = uuid.uuid4()
        other_admin.role = UserRole.ADMIN

        request = factory.delete(f"/api/v1/users/{other_admin.id}/")
        force_authenticate(request, user=mock_admin)

        with patch.object(UserDetailView, 'get_object', return_value=other_admin):
            response = detail_view(request, id=other_admin.id)
            assert response.status_code == status.HTTP_403_FORBIDDEN
            assert "Tenant admin cannot delete" in str(response.data["error"]["message"])
