"""Unit tests for LogoutView ."""

import pytest
from unittest.mock import patch, MagicMock
from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework_simplejwt.exceptions import TokenError
from accounts.views.logout_view import LogoutView


@pytest.fixture
def view():
    return LogoutView.as_view()


@pytest.fixture
def factory():
    return APIRequestFactory()


class TestLogoutView:
    """Unit tests for LogoutView.post()."""

    @patch("accounts.views.logout_view.RefreshToken")
    @patch("accounts.views.logout_view.AccessToken")
    @patch("accounts.views.logout_view.cache")
    def test_logout_success(
        self,
        mock_cache,
        MockAccessToken,
        MockRefreshToken,
        view,
        factory,
        mock_user,
        fake_data,
    ):
        """Valid access + refresh tokens should blacklist both and succeed."""
        jti = fake_data.uuid4()
        mock_access = MagicMock()
        mock_access.get.side_effect = lambda k: {"jti": jti, "exp": 9999999999}[k]
        MockAccessToken.return_value = mock_access

        mock_refresh = MagicMock()
        MockRefreshToken.return_value = mock_refresh

        request = factory.post(
            "/api/v1/auth/logout/",
            {"refresh": fake_data.sha256()},
            HTTP_AUTHORIZATION=f"Bearer {fake_data.sha256()}",
        )
        force_authenticate(request, user=mock_user)
        response = view(request)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["detail"] == "Logged out successfully"
        mock_cache.set.assert_called_once()
        mock_refresh.blacklist.assert_called_once()

    def test_logout_missing_refresh_token(self, view, factory, mock_user, fake_data):
        """Missing refresh token should return 400."""
        request = factory.post(
            "/api/v1/auth/logout/", {}, HTTP_AUTHORIZATION=f"Bearer {fake_data.sha256()}"
        )
        force_authenticate(request, user=mock_user)
        response = view(request)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Refresh token is required" in str(response.data["error"]["details"])

    def test_logout_missing_bearer_header(self, view, factory, fake_data):
        """Missing Authorization header should return 401."""
        request = factory.post("/api/v1/auth/logout/", {"refresh": fake_data.sha256()})
        response = view(request)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Authentication credentials were not provided" in str(
            response.data["error"]["message"]
        )

    @patch("accounts.views.logout_view.RefreshToken")
    def test_logout_invalid_token(self, MockToken, view, factory, mock_user, fake_data):
        """Invalid token should return 401."""

        MockToken.side_effect = TokenError("Token is invalid or expired")

        request = factory.post(
            "/api/v1/auth/logout/",
            {"refresh": fake_data.word()},
            HTTP_AUTHORIZATION=f"Bearer {fake_data.sha256()}",
        )
        force_authenticate(request, user=mock_user)
        response = view(request)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid or expired refresh token" in str(
            response.data["error"]["details"]
        )

    @patch("accounts.views.logout_view.RefreshToken")
    @patch("accounts.views.logout_view.AccessToken")
    @patch("accounts.views.logout_view.cache")
    def test_logout_invalid_refresh_token(
        self,
        mock_cache,
        MockAccessToken,
        MockRefreshToken,
        view,
        factory,
        mock_user,
        fake_data,
    ):
        """Invalid/expired refresh token should return 400."""
        mock_access = MagicMock()
        mock_access.get.side_effect = lambda k: {
            "jti": fake_data.uuid4(),
            "exp": 9999999999,
        }[k]
        MockAccessToken.return_value = mock_access

        MockRefreshToken.side_effect = TokenError("Token is invalid.")

        request = factory.post(
            "/api/v1/auth/logout/",
            {"refresh": fake_data.sha256()},
            HTTP_AUTHORIZATION=f"Bearer {fake_data.sha256()}",
        )
        force_authenticate(request, user=mock_user)
        response = view(request)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid or expired refresh token" in str(
            response.data["error"]["details"]
        )

    @patch("accounts.views.logout_view.AccessToken")
    @patch("accounts.views.logout_view.RefreshToken")
    @patch("accounts.views.logout_view.cache")
    def test_logout_expired_access_still_blacklists_refresh(
        self,
        mock_cache,
        MockRefreshToken,
        MockAccessToken,
        view,
        factory,
        mock_user,
        fake_data,
    ):
        """Expired access token should be caught, but refresh still blacklisted."""
        MockAccessToken.side_effect = TokenError("Token expired")
        mock_refresh = MagicMock()
        MockRefreshToken.return_value = mock_refresh

        request = factory.post(
            "/api/v1/auth/logout/",
            {"refresh": fake_data.sha256()},
            HTTP_AUTHORIZATION=f"Bearer {fake_data.sha256()}",
        )
        force_authenticate(request, user=mock_user)
        response = view(request)

        assert response.status_code == status.HTTP_200_OK
        mock_refresh.blacklist.assert_called_once()
