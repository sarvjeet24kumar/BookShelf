"""Unit tests for ChangePasswordView — all dependencies mocked."""

import pytest
from unittest.mock import patch, MagicMock
from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework.exceptions import ValidationError
from accounts.views.change_password_view import ChangePasswordView


@pytest.fixture
def view():
    return ChangePasswordView.as_view()


@pytest.fixture
def factory():
    return APIRequestFactory()


class TestChangePasswordView:
    """Unit tests for ChangePasswordView.post()."""

    @patch("accounts.views.change_password_view.ChangePasswordSerializer")
    def test_change_password_success(
        self, MockSerializer, view, factory, mock_user, fake_data
    ):
        """Correct current password with valid new password should succeed."""
        mock_ser = MockSerializer.return_value
        mock_ser.is_valid.return_value = True
        new_password = fake_data.password(special_chars=True)
        mock_ser.validated_data = {
            "current_password": fake_data.password(),
            "new_password": new_password,
        }
        mock_user.check_password.return_value = True

        request = factory.post("/api/v1/auth/change-password/", {})
        force_authenticate(request, user=mock_user)
        response = view(request)

        assert response.status_code == status.HTTP_200_OK
        assert "Password changed" in response.data["detail"]
        mock_user.set_password.assert_called_once_with(new_password)
        mock_user.save.assert_called_once()

    @patch("accounts.views.change_password_view.ChangePasswordSerializer")
    def test_change_password_wrong_current(
        self, MockSerializer, view, factory, mock_user, fake_data
    ):
        """Wrong current password should return 400."""
        mock_ser = MockSerializer.return_value
        mock_ser.is_valid.return_value = True
        mock_ser.validated_data = {
            "current_password": fake_data.password(),
            "new_password": fake_data.password(),
        }
        mock_user.check_password.return_value = False

        request = factory.post("/api/v1/auth/change-password/", {})
        force_authenticate(request, user=mock_user)
        response = view(request)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "current_password" in response.data["error"]["details"]

    @patch("accounts.views.change_password_view.ChangePasswordSerializer")
    def test_change_password_invalid_serializer(
        self, MockSerializer, view, factory, mock_user
    ):
        """Invalid serializer data should return 400."""

        mock_ser = MockSerializer.return_value
        mock_ser.is_valid.side_effect = ValidationError({"new_password": ["Too weak."]})

        request = factory.post("/api/v1/auth/change-password/", {})
        force_authenticate(request, user=mock_user)
        response = view(request)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "new_password" in response.data["error"]["details"]
