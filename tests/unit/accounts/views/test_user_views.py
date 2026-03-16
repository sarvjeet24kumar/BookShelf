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
    def test_list_users_as_superadmin(
        self, MockUser, list_view, factory, mock_super_admin
    ):
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

        request = factory.post(
            "/api/v1/users/",
            {
                "username": fake_data.user_name(),
                "email": fake_data.email(),
                "password": fake_data.password(special_chars=True),
            },
        )
        force_authenticate(request, user=mock_admin)

        with patch.object(UserView, "get_serializer") as mock_get_ser:
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
    def test_create_user_duplicate_email(
        self, MockUser, list_view, factory, mock_admin, fake_data
    ):
        """Duplicate email should return 400."""
        MockUser.all_objects.filter.return_value.exists.return_value = True

        dup_email = fake_data.email()
        request = factory.post(
            "/api/v1/users/",
            {
                "username": fake_data.user_name(),
                "email": dup_email,
                "password": fake_data.password(special_chars=True),
            },
        )
        force_authenticate(request, user=mock_admin)

        with patch.object(UserView, "get_serializer") as mock_get_ser:
            mock_ser = MagicMock()
            mock_ser.is_valid.return_value = True
            mock_ser.validated_data = {"email": dup_email}
            mock_get_ser.return_value = mock_ser

            response = list_view(request)
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert "A user with this email already exists." in str(
                response.data["error"]["details"]
            )

    @patch("accounts.views.user_views.User")
    def test_create_admin_as_superadmin_requires_tenant(
        self, MockUser, list_view, factory, mock_super_admin, fake_data
    ):
        """Super admin creating admin without tenant should return 400."""
        new_email = fake_data.email()
        request = factory.post(
            "/api/v1/users/",
            {
                "username": fake_data.user_name(),
                "email": new_email,
                "password": fake_data.password(special_chars=True),
            },
        )
        force_authenticate(request, user=mock_super_admin)

        with patch.object(UserView, "get_serializer") as mock_get_ser:
            mock_ser = MagicMock()
            mock_ser.is_valid.return_value = True
            mock_ser.validated_data = {"email": new_email, "tenant": None}
            mock_get_ser.return_value = mock_ser

            response = list_view(request)
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert "Tenant" in str(response.data["error"]["details"])

    @patch("accounts.views.user_views.email_verification_service")
    def test_create_admin_as_superadmin_success(
        self, mock_email_svc, list_view, factory, mock_super_admin, fake_data, mock_tenant
    ):
        """Super admin creating an admin with a tenant should return 200."""
        new_email = fake_data.email()
        request = factory.post(
            "/api/v1/users/",
            {
                "username": fake_data.user_name(),
                "email": new_email,
                "password": fake_data.password(special_chars=True),
                "tenant": str(mock_tenant.id),
            },
            format="json",
        )
        force_authenticate(request, user=mock_super_admin)

        with patch('accounts.views.user_views.User.all_objects.filter') as mock_filter:
            mock_filter.return_value.exists.return_value = False
            
            with patch.object(UserView, "get_serializer") as mock_get_ser:
                mock_ser = MagicMock()
                mock_ser.is_valid.return_value = True
                mock_ser.validated_data = {"email": new_email, "tenant": mock_tenant}
                
                mock_saved_user = MagicMock()
                mock_saved_user.username = "newadmin"
                mock_saved_user.email = new_email
                mock_ser.save.return_value = mock_saved_user
                
                mock_get_ser.return_value = mock_ser

                response = list_view(request)
                assert response.status_code == status.HTTP_200_OK


class TestUserDetailViewUpdate:
    """Unit tests for UserDetailView PUT (update user)."""

    def test_update_email_blocked(
        self, detail_view, factory, mock_user, mock_admin, fake_data
    ):
        """Attempting to update email should return 403."""
        request = factory.put(
            f"/api/v1/users/{mock_user.id}/",
            {"email": fake_data.email()},
            format="json",
        )
        force_authenticate(request, user=mock_admin)

        with patch.object(UserDetailView, "get_object", return_value=mock_user):
            response = detail_view(request, id=mock_user.id)
            assert response.status_code == status.HTTP_403_FORBIDDEN
            assert "Email and role cannot be changed." in str(
                response.data["error"]["message"]
            )

    def test_update_role_blocked(self, detail_view, factory, mock_user, mock_admin):
        """Attempting to update role should return 403."""
        request = factory.put(
            f"/api/v1/users/{mock_user.id}/", {"role": "admin"}, format="json"
        )
        force_authenticate(request, user=mock_admin)

        with patch.object(UserDetailView, "get_object", return_value=mock_user):
            response = detail_view(request, id=mock_user.id)
            assert response.status_code == status.HTTP_403_FORBIDDEN
            assert "Email and role cannot be changed." in str(
                response.data["error"]["message"]
            )

    def test_regular_user_cannot_update_restricted_fields(
        self, detail_view, factory, mock_user
    ):
        """Regular user cannot update is_active — should return 403."""
        request = factory.put(
            f"/api/v1/users/{mock_user.id}/", {"is_active": False}, format="json"
        )
        mock_user.role = UserRole.USER
        force_authenticate(request, user=mock_user)

        with patch.object(UserDetailView, "get_object", return_value=mock_user):
            response = detail_view(request, id=mock_user.id)
            assert response.status_code == status.HTTP_403_FORBIDDEN
            assert (
                "You cannot update restricted fields (is_active, deleted_at)."
                in str(response.data["error"]["message"])
            )

    def test_tenant_admin_cannot_update_other_admin(self, detail_view, factory, mock_admin):
        """Tenant admin updating another admin should return 403."""
        other_admin = MagicMock()
        other_admin.id = uuid.uuid4()
        other_admin.role = UserRole.ADMIN
        
        request = factory.put(
            f"/api/v1/users/{other_admin.id}/", {"first_name": "New"}, format="json"
        )
        force_authenticate(request, user=mock_admin)

        with patch.object(UserDetailView, "get_object", return_value=other_admin):
            response = detail_view(request, id=other_admin.id)
            assert response.status_code == status.HTTP_403_FORBIDDEN
            assert "Tenant admin cannot update other admin accounts" in str(response.data["error"]["message"])

    @patch("accounts.views.user_views.User")
    def test_update_duplicate_username(self, MockUser, detail_view, factory, mock_user, mock_admin):
        """Duplicate username update should return 400."""
        MockUser.all_objects.filter.return_value.exists.return_value = True
        
        request = factory.put(
            f"/api/v1/users/{mock_user.id}/", {"username": "taken_username"}, format="json"
        )
        force_authenticate(request, user=mock_admin)

        with patch.object(UserDetailView, "get_object", return_value=mock_user):
            response = detail_view(request, id=mock_user.id)
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert "already taken" in str(response.data["error"]["details"]["username"])

    @patch("accounts.views.user_views.blacklist_user_tokens")
    def test_update_user_success_and_blacklist_tokens(self, mock_blacklist, detail_view, factory, mock_user, mock_admin):
        """Updating user successfully and blacklisting tokens if deactivated."""
        request = factory.put(
            f"/api/v1/users/{mock_user.id}/", {"first_name": "Updated"}, format="json"
        )
        force_authenticate(request, user=mock_admin)
        
        mock_user.is_active = True # Originally active

        with patch.object(UserDetailView, "get_object", return_value=mock_user):
            with patch.object(UserDetailView, "get_serializer") as mock_ser:
                mock_ser_instance = MagicMock()
                mock_ser_instance.is_valid.return_value = True
                mock_ser_instance.data = {"first_name": "Updated"}
                
                # Mock updated user as inactive to trigger blacklist
                updated_user = MagicMock()
                updated_user.is_active = False 
                mock_ser_instance.save.return_value = updated_user
                
                mock_ser.return_value = mock_ser_instance

                response = detail_view(request, id=mock_user.id)
                assert response.status_code == status.HTTP_200_OK
                mock_blacklist.assert_called_once_with(updated_user)


class TestUserDetailViewDestroy:
    """Unit tests for UserDetailView DELETE."""

    @patch("accounts.views.user_views.blacklist_user_tokens")
    def test_admin_cannot_delete_self(
        self, mock_blacklist, detail_view, factory, mock_admin
    ):
        """Admin deleting themselves should return 403."""
        request = factory.delete(f"/api/v1/users/{mock_admin.id}/")
        force_authenticate(request, user=mock_admin)

        with patch.object(UserDetailView, "get_object", return_value=mock_admin):
            response = detail_view(request, id=mock_admin.id)
            assert response.status_code == status.HTTP_403_FORBIDDEN
            assert "Admins cannot delete their own account." in str(
                response.data["error"]["message"]
            )

    @patch("accounts.views.user_views.transaction")
    @patch("accounts.views.user_views.blacklist_user_tokens")
    def test_admin_delete_user_success(
        self,
        mock_blacklist,
        mock_transaction,
        detail_view,
        factory,
        mock_admin,
        mock_user,
    ):
        """Admin deleting a regular user should return 204."""
        mock_transaction.atomic.return_value.__enter__ = MagicMock()
        mock_transaction.atomic.return_value.__exit__ = MagicMock(return_value=False)

        request = factory.delete(f"/api/v1/users/{mock_user.id}/")
        force_authenticate(request, user=mock_admin)

        with patch.object(UserDetailView, "get_object", return_value=mock_user):
            response = detail_view(request, id=mock_user.id)
            assert response.status_code == status.HTTP_204_NO_CONTENT
            mock_user.soft_delete.assert_called_once()
            mock_blacklist.assert_called_once_with(mock_user)

    @patch("accounts.views.user_views.transaction")
    @patch("accounts.views.user_views.blacklist_user_tokens")
    def test_user_self_delete(
        self,
        mock_blacklist,
        mock_transaction,
        detail_view,
        factory,
        mock_user,
    ):
        """User deleting themselves should return 204."""
        mock_transaction.atomic.return_value.__enter__ = MagicMock()
        mock_transaction.atomic.return_value.__exit__ = MagicMock(return_value=False)

        mock_user.role = UserRole.USER
        request = factory.delete(f"/api/v1/users/{mock_user.id}/")
        force_authenticate(request, user=mock_user)

        with patch.object(UserDetailView, "get_object", return_value=mock_user):
            response = detail_view(request, id=mock_user.id)
            assert response.status_code == status.HTTP_204_NO_CONTENT
            mock_user.soft_delete.assert_called_once()
            assert mock_user.is_active is False
            mock_user.save.assert_called_once()
            mock_blacklist.assert_called_once_with(mock_user)


class TestUserDetailViewRetrieve:
    """Unit tests for UserDetailView GET and methods."""

    def test_retrieve_user(self, detail_view, factory, mock_user, mock_admin):
        """GET /users/{id}/ should return user data."""
        request = factory.get(f"/api/v1/users/{mock_user.id}/")
        force_authenticate(request, user=mock_admin)
        with patch.object(UserDetailView, 'get_object', return_value=mock_user):
            with patch.object(UserDetailView, 'get_serializer') as mock_ser:
                mock_ser_instance = MagicMock()
                mock_ser_instance.data = {"username": "test"}
                mock_ser.return_value = mock_ser_instance
                response = detail_view(request, id=mock_user.id)
                assert response.status_code == status.HTTP_200_OK
                assert response.data == {"username": "test"}

    @patch("accounts.views.user_views.User.objects.all")
    @patch("common.permissions.IsOwnerOrAdmin.has_object_permission", return_value=True)
    def test_get_queryset_and_serializer_user_role(self, mock_has_perm, mock_all, detail_view, factory, mock_user):
        """Test get_queryset and get_serializer logic."""
        request = factory.get(f"/api/v1/users/{mock_user.id}/")
        mock_user.role = UserRole.USER
        force_authenticate(request, user=mock_user)
        
        mock_qs = MagicMock()
        mock_qs.get.return_value = mock_user
        mock_all.return_value = mock_qs
            
        with patch('accounts.views.user_views.RetrieveUpdateDestroyAPIView.get_serializer') as mock_super_get_serializer:
            mock_ser_instance = MagicMock()
            mock_ser_instance.data = {"username": "test"}
            mock_super_get_serializer.return_value = mock_ser_instance
                
            response = detail_view(request, id=mock_user.id)
            assert response.status_code == status.HTTP_200_OK
                
            mock_all.assert_called_once()
            mock_super_get_serializer.assert_called_once()
            assert mock_super_get_serializer.call_args[1].get('exclude_fields') == ["deleted_at", "is_active"]
