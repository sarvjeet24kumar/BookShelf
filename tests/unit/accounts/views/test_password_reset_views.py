"""Unit tests for ForgotPasswordView and ResetPasswordView — all dependencies mocked."""

import pytest
import uuid
from unittest.mock import patch, MagicMock
from rest_framework import status
from rest_framework.test import APIRequestFactory
from rest_framework.exceptions import ValidationError
from accounts.views.password_reset_views import ForgotPasswordView, ResetPasswordView


@pytest.fixture
def forgot_view():
    return ForgotPasswordView.as_view()


@pytest.fixture
def reset_view():
    return ResetPasswordView.as_view()


@pytest.fixture
def factory():
    return APIRequestFactory()


class TestForgotPasswordView:
    """Unit tests for ForgotPasswordView.post()."""

    @patch("accounts.views.password_reset_views.password_reset_service")
    @patch("accounts.views.password_reset_views.find_user_with_validation")
    @patch("accounts.views.password_reset_views.get_tenant_from_header")
    def test_forgot_password_success(
        self,
        mock_get_tenant,
        mock_find_user,
        mock_reset_svc,
        forgot_view,
        factory,
        mock_user,
        mock_tenant,
        fake_data,
    ):
        """Existing user should trigger password reset token creation."""
        mock_get_tenant.return_value = mock_tenant
        mock_find_user.return_value = mock_user
        mock_reset_svc.create.return_value = fake_data.sha256()

        request = factory.post(
            "/api/v1/auth/forgot-password/", {"email": mock_user.email}
        )
        response = forgot_view(request)

        assert response.status_code == status.HTTP_200_OK
        assert "reset link has been sent" in response.data["detail"]
        mock_reset_svc.create.assert_called_once()

    @patch("accounts.views.password_reset_views.find_user_with_validation")
    @patch("accounts.views.password_reset_views.get_tenant_from_header")
    def test_forgot_password_user_not_found_silent_response(
        self,
        mock_get_tenant,
        mock_find_user,
        forgot_view,
        factory,
        mock_tenant,
        fake_data,
    ):
        """Non-existent user should return 200 (silent for security)."""
        mock_get_tenant.return_value = mock_tenant
        mock_find_user.return_value = None

        request = factory.post(
            "/api/v1/auth/forgot-password/", {"email": fake_data.email()}
        )
        response = forgot_view(request)
        assert response.status_code == status.HTTP_200_OK
        assert "reset link has been sent" in response.data["detail"]


class TestResetPasswordView:
    """Unit tests for ResetPasswordView."""

    @patch("accounts.views.password_reset_views.password_reset_service")
    def test_reset_password_get_valid_token_renders_form(
        self, mock_reset_svc, reset_view, factory, fake_data
    ):
        """Valid token should render the password reset form."""
        user_id = str(uuid.uuid4())
        mock_reset_svc.verify.return_value = (True, "", user_id)

        request = factory.get(
            "/api/v1/auth/reset-password/", {"token": fake_data.sha256()}
        )
        response = reset_view(request)
        assert response.status_code == status.HTTP_200_OK
        assert b"Set New Password" in response.content

    @patch("accounts.views.password_reset_views.password_reset_service")
    def test_reset_password_get_invalid_token_renders_error(
        self, mock_reset_svc, reset_view, factory, fake_data
    ):
        """Invalid/expired token should render error page."""
        mock_reset_svc.verify.return_value = (False, "Token expired.", None)

        request = factory.get(
            "/api/v1/auth/reset-password/", {"token": fake_data.sha256()}
        )
        response = reset_view(request)
        assert response.status_code == status.HTTP_200_OK
        assert b"Invalid Link" in response.content

    def test_reset_password_get_no_token(self, reset_view, factory):
        """Missing token in GET should render error."""
        request = factory.get("/api/v1/auth/reset-password/")
        response = reset_view(request)
        assert response.status_code == status.HTTP_200_OK
        assert b"Missing or invalid token" in response.content

    def test_reset_password_post_no_token(self, reset_view, factory):
        """Missing token in POST should render error."""
        request = factory.post("/api/v1/auth/reset-password/", {"password": "NewPassword123!", "confirm_password": "NewPassword123!"})
        response = reset_view(request)
        assert response.status_code == status.HTTP_200_OK
        assert b"Reset token is required." in response.content

    def test_reset_password_post_missing_passwords(self, reset_view, factory):
        """Missing passwords in POST should render error."""
        request = factory.post("/api/v1/auth/reset-password/?token=validtoken", {})
        response = reset_view(request)
        assert response.status_code == status.HTTP_200_OK
        assert b"Both password and confirmation are required." in response.content

    def test_reset_password_post_mismatched_passwords(self, reset_view, factory):
        """Mismatched passwords in POST should render error."""
        request = factory.post("/api/v1/auth/reset-password/?token=validtoken", {"password": "NewPassword123!", "confirm_password": "OtherPassword123!"})
        response = reset_view(request)
        assert response.status_code == status.HTTP_200_OK
        assert b"Passwords do not match." in response.content

    @patch("accounts.views.password_reset_views.password_reset_service")
    def test_reset_password_post_invalid_token(self, mock_reset_svc, reset_view, factory):
        """Invalid token verification should render error."""
        mock_reset_svc.verify.return_value = (False, "Token expired.", None)
        request = factory.post("/api/v1/auth/reset-password/?token=invalidtoken", {"password": "NewPassword123!", "confirm_password": "NewPassword123!"})
        response = reset_view(request)
        assert response.status_code == status.HTTP_200_OK
        assert b"Token expired." in response.content

    @patch("accounts.views.password_reset_views.User.all_objects.filter")
    @patch("accounts.views.password_reset_views.password_reset_service")
    def test_reset_password_post_user_not_found(self, mock_reset_svc, mock_user_filter, reset_view, factory):
        """User not found should render error."""
        user_id = str(uuid.uuid4())
        mock_reset_svc.verify.return_value = (True, "", user_id)
        
        mock_qs = MagicMock()
        mock_qs.first.return_value = None
        mock_user_filter.return_value = mock_qs

        request = factory.post("/api/v1/auth/reset-password/?token=validtoken", {"password": "NewPassword123!", "confirm_password": "NewPassword123!"})
        response = reset_view(request)
        assert response.status_code == status.HTTP_200_OK
        assert b"User not found." in response.content

    @patch("accounts.views.password_reset_views.User.all_objects.filter")
    @patch("accounts.views.password_reset_views.password_reset_service")
    def test_reset_password_post_success(self, mock_reset_svc, mock_user_filter, reset_view, factory, mock_user):
        """Valid data should reset password and render success."""
        user_id = str(uuid.uuid4())
        mock_reset_svc.verify.return_value = (True, "", user_id)
        
        mock_qs = MagicMock()
        mock_qs.first.return_value = mock_user
        mock_user_filter.return_value = mock_qs

        request = factory.post("/api/v1/auth/reset-password/?token=validtoken", {"password": "NewPassword123!", "confirm_password": "NewPassword123!"})
        response = reset_view(request)
        
        assert response.status_code == status.HTTP_200_OK
        mock_user.set_password.assert_called_once_with("NewPassword123!")
        mock_user.save.assert_called_once_with(update_fields=["password", "updated_at"])
        mock_reset_svc.cleanup.assert_called_once_with("validtoken")
