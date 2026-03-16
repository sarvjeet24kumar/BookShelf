"""Unit tests for VerifyLoginView — all dependencies mocked."""
import pytest
from unittest.mock import patch, MagicMock
from rest_framework import status
from rest_framework.test import APIRequestFactory
from accounts.views.authentication_views import VerifyLoginView


@pytest.fixture
def view():
    return VerifyLoginView.as_view()


@pytest.fixture
def factory():
    return APIRequestFactory()


class TestVerifyLoginView:
    """Unit tests for VerifyLoginView.post()."""

    @patch("accounts.views.authentication_views.RefreshToken")
    @patch("accounts.views.authentication_views.login_otp_service")
    @patch("accounts.views.authentication_views.find_user_with_validation")
    @patch("accounts.views.authentication_views.get_tenant_from_header")
    def test_verify_login_success_returns_tokens(
        self, mock_get_tenant, mock_find_user, mock_otp_service, MockRefresh,
        view, factory, mock_user, mock_tenant, fake_data
    ):
        """Valid OTP should return access and refresh tokens."""
        mock_get_tenant.return_value = mock_tenant
        mock_find_user.return_value = mock_user
        mock_otp_service.verify.return_value = (True, "")

        access_token = fake_data.sha256()
        refresh_token = fake_data.sha256()
        mock_refresh = MagicMock()
        mock_refresh.access_token = access_token
        mock_refresh.__str__ = MagicMock(return_value=refresh_token)
        MockRefresh.for_user.return_value = mock_refresh

        request = factory.post("/api/v1/auth/verify-login/", {
            "username": mock_user.username, "otp": fake_data.msisdn()[:6]
        })
        response = view(request)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["access"] == access_token
        assert response.data["refresh"] == refresh_token
        mock_otp_service.cleanup.assert_called_once()

    @patch("accounts.views.authentication_views.find_user_with_validation")
    @patch("accounts.views.authentication_views.get_tenant_from_header")
    def test_verify_login_user_not_found(
        self, mock_get_tenant, mock_find_user, view, factory, mock_tenant, fake_data
    ):
        """Non-existent user should return 400."""
        mock_get_tenant.return_value = mock_tenant
        mock_find_user.return_value = None

        request = factory.post("/api/v1/auth/verify-login/", {
            "username": fake_data.user_name(), "otp": fake_data.msisdn()[:6]
        })
        response = view(request)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid credentials or OTP." in str(response.data["error"]["details"])

    @patch("accounts.views.authentication_views.login_otp_service")
    @patch("accounts.views.authentication_views.find_user_with_validation")
    def test_verify_login_invalid_otp(self, mock_find_user, mock_otp_svc, view, factory):
        """Invalid OTP should return 400."""
        mock_user = MagicMock()
        mock_find_user.return_value = mock_user
        mock_otp_svc.verify.return_value = (False, "Invalid OTP.")

        request = factory.post("/api/v1/auth/verify-login/", {"email": "user@example.com", "otp": "000000"})
        response = view(request)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid OTP." in str(response.data["error"]["details"])

    @patch("accounts.views.authentication_views.login_otp_service")
    @patch("accounts.views.authentication_views.find_user_with_validation")
    def test_verify_login_expired_otp(self, mock_find_user, mock_otp_svc, view, factory):
        """Expired OTP should return 400."""
        mock_user = MagicMock()
        mock_find_user.return_value = mock_user
        mock_otp_svc.verify.return_value = (False, "OTP expired.")

        request = factory.post("/api/v1/auth/verify-login/", {"email": "user@example.com", "otp": "111111"})
        response = view(request)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "OTP expired." in str(response.data["error"]["details"])
