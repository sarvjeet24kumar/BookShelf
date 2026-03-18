"""Unit tests for LoginView ."""

import pytest
from unittest.mock import patch, MagicMock
from rest_framework import status
from rest_framework.test import APIRequestFactory
from accounts.views.authentication_views import LoginView


@pytest.fixture
def view():
    return LoginView.as_view()


@pytest.fixture
def factory():
    return APIRequestFactory()


def _setup_login_mocks(
    MockSerializer,
    mock_get_tenant,
    mock_tenant,
    email=None,
    password=None,
    fake_data=None,
):
    """Helper to set up common login mocks."""
    mock_get_tenant.return_value = mock_tenant
    mock_ser = MockSerializer.return_value
    mock_ser.is_valid.return_value = True
    mock_ser.validated_data = {
        "email": email or fake_data.email(),
        "username": None,
        "password": password or fake_data.password(special_chars=True),
    }
    return mock_ser


class TestLoginView:
    """Unit tests for LoginView.post()."""

    @patch("accounts.views.authentication_views.login_otp_service")
    @patch("accounts.views.authentication_views.authenticate")
    @patch("accounts.views.authentication_views.find_user")
    @patch("accounts.views.authentication_views.get_tenant_from_header")
    @patch("accounts.views.authentication_views.LoginSerializer")
    def test_login_success_sends_otp(
        self,
        MockSerializer,
        mock_get_tenant,
        mock_find_user,
        mock_authenticate,
        mock_otp_service,
        view,
        factory,
        mock_user,
        mock_tenant,
        fake_data,
    ):
        """Valid credentials should trigger OTP creation."""
        _setup_login_mocks(
            MockSerializer,
            mock_get_tenant,
            mock_tenant,
            email=mock_user.email,
            fake_data=fake_data,
        )
        mock_find_user.return_value = mock_user
        mock_authenticate.return_value = mock_user

        request = factory.post("/api/v1/auth/login/", {})
        response = view(request)

        assert response.status_code == status.HTTP_200_OK
        assert (
            response.data["detail"] == "OTP sent to your email. Please verify to login."
        )
        mock_otp_service.create.assert_called_once()

    @patch("accounts.views.authentication_views.find_user")
    @patch("accounts.views.authentication_views.get_tenant_from_header")
    @patch("accounts.views.authentication_views.LoginSerializer")
    def test_login_user_not_found(
        self,
        MockSerializer,
        mock_get_tenant,
        mock_find_user,
        view,
        factory,
        mock_tenant,
        fake_data,
    ):
        """Non-existent user should return 401."""
        _setup_login_mocks(
            MockSerializer, mock_get_tenant, mock_tenant, fake_data=fake_data
        )
        mock_find_user.return_value = None

        request = factory.post("/api/v1/auth/login/", {})
        response = view(request)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data["error"]["message"] == "Invalid credentials."

    @patch("accounts.views.authentication_views.find_user")
    @patch("accounts.views.authentication_views.get_tenant_from_header")
    def test_login_deleted_user(
        self, mock_get_tenant, mock_find_user, view, factory, mock_tenant, fake_data
    ):
        """Deleted user should get 401."""
        mock_user = MagicMock()
        mock_user.deleted_at = fake_data.date_time_between(start_date='-1y', end_date='now')
        mock_find_user.return_value = mock_user

        request = factory.post(
            "/api/v1/auth/login/", {"email": fake_data.email(), "password": fake_data.password()}
        )
        response = view(request)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "account has been deleted" in response.data["error"]["message"]

    @patch("accounts.views.authentication_views.find_user")
    @patch("accounts.views.authentication_views.get_tenant_from_header")
    def test_login_unverified_email(
        self, mock_get_tenant, mock_find_user, view, factory, mock_tenant, fake_data
    ):
        """Unverified email user should get 401."""
        mock_user = MagicMock()
        mock_user.deleted_at = None
        mock_user.is_email_verified = False
        mock_find_user.return_value = mock_user

        request = factory.post(
            "/api/v1/auth/login/",
            {"email": fake_data.email(), "password": fake_data.password()},
        )
        response = view(request)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "verify your email" in response.data["error"]["message"]

    @patch("accounts.views.authentication_views.find_user")
    @patch("accounts.views.authentication_views.get_tenant_from_header")
    def test_login_inactive_user(
        self, mock_get_tenant, mock_find_user, view, factory, mock_tenant, fake_data
    ):
        """Suspended user should get 401."""
        mock_user = MagicMock()
        mock_user.deleted_at = None
        mock_user.is_email_verified = True
        mock_user.is_active = False
        mock_find_user.return_value = mock_user

        request = factory.post(
            "/api/v1/auth/login/",
            {"email": fake_data.email(), "password": fake_data.password()},
        )
        response = view(request)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "account has been suspended" in response.data["error"]["message"]

    @patch("accounts.views.authentication_views.authenticate")
    @patch("accounts.views.authentication_views.find_user")
    @patch("accounts.views.authentication_views.get_tenant_from_header")
    def test_login_wrong_password(
        self,
        mock_get_tenant,
        mock_find_user,
        mock_authenticate,
        view,
        factory,
        mock_tenant,
        fake_data,
    ):
        """Wrong password should return 401."""
        mock_user = MagicMock()
        mock_user.deleted_at = None
        mock_user.is_email_verified = True
        mock_user.is_active = True
        mock_find_user.return_value = mock_user
        mock_authenticate.return_value = None

        request = factory.post(
            "/api/v1/auth/login/",
            {"email": fake_data.email(), "password": fake_data.password()},
        )
        response = view(request)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data["error"]["message"] == "Invalid credentials."
