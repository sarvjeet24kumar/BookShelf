"""Unit tests for SignupView — all dependencies mocked."""
import pytest
from unittest.mock import patch, MagicMock
from rest_framework import status
from rest_framework.test import APIRequestFactory
from accounts.views.registration_views import SignupView



@pytest.fixture
def view():
    return SignupView.as_view()


@pytest.fixture
def factory():
    return APIRequestFactory()


class TestSignupView:
    """Unit tests for SignupView.post()."""

    @patch("accounts.views.registration_views.email_verification_service")
    @patch("accounts.views.registration_views.User")
    @patch("accounts.views.registration_views.SignupSerializer")
    @patch("accounts.views.registration_views.get_tenant_from_header")
    def test_signup_success(
        self, mock_get_tenant, MockSerializer, MockUser, mock_email_svc,
        view, factory, mock_tenant, fake_data
    ):
        """Valid signup data with no duplicate email should create user and send OTP."""
        mock_get_tenant.return_value = mock_tenant
        email = fake_data.email()

        mock_ser = MockSerializer.return_value
        mock_ser.is_valid.return_value = True
        mock_ser.validated_data = {"email": email}

        MockUser.all_objects.filter.return_value.first.return_value = None

        mock_saved_user = MagicMock()
        mock_saved_user.username = fake_data.user_name()
        mock_saved_user.email = email
        mock_ser.save.return_value = mock_saved_user

        request = factory.post("/api/v1/auth/signup/", {})
        response = view(request)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["detail"] == "Verification code sent to your email."
        mock_ser.save.assert_called_once_with(tenant=mock_tenant)
        mock_email_svc.create.assert_called_once()

    @patch("accounts.views.registration_views.User")
    @patch("accounts.views.registration_views.SignupSerializer")
    @patch("accounts.views.registration_views.get_tenant_from_header")
    def test_signup_duplicate_email(
        self, mock_get_tenant, MockSerializer, MockUser, view, factory, mock_tenant, fake_data
    ):
        """Duplicate email in same tenant should return 400."""
        mock_get_tenant.return_value = mock_tenant

        mock_ser = MockSerializer.return_value
        mock_ser.is_valid.return_value = True
        mock_ser.validated_data = {"email": fake_data.email()}

        existing_user = MagicMock()
        MockUser.all_objects.filter.return_value.first.return_value = existing_user

        request = factory.post("/api/v1/auth/signup/", {})
        response = view(request)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "cannot be created" in str(response.data["error"]["details"])

    # Removed @patch("accounts.views.registration_views.SignupSerializer")
    def test_signup_invalid_data(
        self, view, factory, mock_tenant # Modified parameters
    ):
        """Invalid data should return 400."""
        # Removed from rest_framework.exceptions import ValidationError and serializer mocking
        request = factory.post("/api/v1/auth/signup/", { # Modified request data
            "email": "invalid-email",
            "password": "short",
            "username": ""
        })
        response = view(request) # Changed 'view' to 'signup_view'
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "error" in response.data # Modified assertion
        assert "details" in response.data["error"] # Modified assertion
