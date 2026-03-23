"""Unit tests for VerifyEmailView and ResendOTPView ."""

import pytest
from unittest.mock import patch, MagicMock
from rest_framework import status
from rest_framework.test import APIRequestFactory
from accounts.views.email_verification_views import VerifyEmailView, ResendOTPView


@pytest.fixture
def verify_view():
    return VerifyEmailView.as_view()


@pytest.fixture
def resend_view():
    return ResendOTPView.as_view()


@pytest.fixture
def factory():
    return APIRequestFactory()


class TestVerifyEmailView:
    """Unit tests for VerifyEmailView.post()."""

    @patch("accounts.views.email_verification_views.email_verification_service")
    @patch("accounts.views.email_verification_views.find_user_with_validation")
    @patch("accounts.views.email_verification_views.get_tenant_from_header")
    def test_verify_email_success(
        self,
        mock_get_tenant,
        mock_find_user,
        mock_email_svc,
        verify_view,
        factory,
        mock_user,
        mock_tenant,
        fake_data,
    ):
        """Valid OTP should verify email and activate user."""
        mock_user.is_email_verified = False
        mock_get_tenant.return_value = mock_tenant
        mock_find_user.return_value = mock_user
        mock_email_svc.verify.return_value = (True, "")

        request = factory.post(
            "/api/v1/auth/verify-email/",
            {"username": mock_user.username, "otp": fake_data.msisdn()[:6]},
        )
        response = verify_view(request)

        assert response.status_code == status.HTTP_201_CREATED
        assert mock_user.is_email_verified is True
        assert mock_user.is_active is True
        mock_user.save.assert_called_once()
        mock_email_svc.cleanup.assert_called_once()

    @patch("accounts.views.email_verification_views.find_user_with_validation")
    @patch("accounts.views.email_verification_views.get_tenant_from_header")
    def test_verify_email_user_not_found(
        self,
        mock_get_tenant,
        mock_find_user,
        verify_view,
        factory,
        mock_tenant,
        fake_data,
    ):
        """Non-existent user should return 400."""
        mock_get_tenant.return_value = mock_tenant
        mock_find_user.return_value = None

        request = factory.post(
            "/api/v1/auth/verify-email/",
            {"username": fake_data.user_name(), "otp": fake_data.msisdn()[:6]},
        )
        response = verify_view(request)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "No pending signup found." in str(response.data["error"]["details"])

    @patch("accounts.views.email_verification_views.find_user_with_validation")
    @patch("accounts.views.email_verification_views.get_tenant_from_header")
    def test_verify_email_already_verified(
        self,
        mock_get_tenant,
        mock_find_user,
        verify_view,
        factory,
        mock_user,
        mock_tenant,
        fake_data,
    ):
        """Already verified user should return 400."""
        mock_user.is_email_verified = True
        mock_get_tenant.return_value = mock_tenant
        mock_find_user.return_value = mock_user

        request = factory.post(
            "/api/v1/auth/verify-email/",
            {"username": mock_user.username, "otp": fake_data.msisdn()[:6]},
        )
        response = verify_view(request)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Email already verified." in str(response.data["error"]["details"])

    @patch("accounts.views.email_verification_views.email_verification_service")
    @patch("accounts.views.email_verification_views.find_user_with_validation")
    @patch("accounts.views.email_verification_views.get_tenant_from_header")
    def test_verify_email_invalid_otp(
        self,
        mock_get_tenant,
        mock_find_user,
        mock_email_svc,
        verify_view,
        factory,
        mock_user,
        mock_tenant,
        fake_data,
    ):
        """Invalid OTP from service should return 400."""
        mock_user.is_email_verified = False
        mock_get_tenant.return_value = mock_tenant
        mock_find_user.return_value = mock_user
        mock_email_svc.verify.return_value = (False, "Invalid OTP.")

        request = factory.post(
            "/api/v1/auth/verify-email/",
            {"username": mock_user.username, "otp": fake_data.msisdn()[:6]},
        )
        response = verify_view(request)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid OTP." in str(response.data["error"]["details"])


class TestResendOTPView:
    """Unit tests for ResendOTPView.post()."""

    @patch("accounts.views.email_verification_views.email_verification_service")
    @patch("accounts.views.email_verification_views.find_user_with_validation")
    @patch("accounts.views.email_verification_views.get_tenant_from_header")
    def test_resend_otp_success(
        self,
        mock_get_tenant,
        mock_find_user,
        mock_email_svc,
        resend_view,
        factory,
        mock_user,
        mock_tenant,
    ):
        """Resend OTP for unverified user should send new OTP."""
        mock_user.is_email_verified = False
        mock_get_tenant.return_value = mock_tenant
        mock_find_user.return_value = mock_user

        request = factory.post(
            "/api/v1/auth/resend-otp/", {"username": mock_user.username}
        )
        response = resend_view(request)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["detail"] == "New verification code sent to your email."
        mock_email_svc.create.assert_called_once()

    @patch("accounts.views.email_verification_views.find_user_with_validation")
    @patch("accounts.views.email_verification_views.get_tenant_from_header")
    def test_resend_otp_user_not_found_silent_response(
        self,
        mock_get_tenant,
        mock_find_user,
        resend_view,
        factory,
        mock_tenant,
        fake_data,
    ):
        """Non-existent user should return 200 (silent for security)."""
        mock_get_tenant.return_value = mock_tenant
        mock_find_user.return_value = None

        request = factory.post("/api/v1/auth/resend-otp/", {"email": fake_data.email()})
        response = resend_view(request)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["detail"] == "New verification code sent to your email."

    @patch("accounts.views.email_verification_views.find_user_with_validation")
    @patch("accounts.views.email_verification_views.get_tenant_from_header")
    def test_resend_otp_already_verified(
        self,
        mock_get_tenant,
        mock_find_user,
        resend_view,
        factory,
        mock_user,
        mock_tenant,
    ):
        """Already verified user should return 400."""
        mock_user.is_email_verified = True
        mock_get_tenant.return_value = mock_tenant
        mock_find_user.return_value = mock_user

        request = factory.post(
            "/api/v1/auth/resend-otp/", {"username": mock_user.username}
        )
        response = resend_view(request)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already verified" in str(response.data["error"]["details"])
