import pytest
from django.urls import reverse
from rest_framework import status
from unittest.mock import patch
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from tests.factories.account_factories import UserFactory

User = get_user_model()

@pytest.mark.django_db
class TestAccountViews:
    """Integration tests for Accounts."""

    @patch("accounts.views.registration_views.email_verification_service.create")
    def test_signup_success(self, mock_email_create, api_client, tenant, faker):
        url = reverse("signup")
        username = faker.user_name()
        password = f"{faker.password(length=10, special_chars=True, digits=True)}A1!"
        data = {
            "username": username,
            "password": password,
            "password_confirm": password,
            "email": faker.email(),
            "first_name": faker.first_name(),
            "last_name": faker.last_name(),
            "phone_no": f"+91{faker.msisdn()[3:]}",
        }
        response = api_client.post(url, data, HTTP_TENANT_ID=str(tenant.id))
        assert response.status_code == status.HTTP_200_OK
        assert User.objects.filter(username=username).exists()

    @patch("accounts.views.authentication_views.login_otp_service.create")
    def test_login_otp_sent(self, mock_otp_create, api_client, user, tenant, faker):
        password = f"{faker.password(length=10)}A1!"
        user.set_password(password)
        user.save()
        
        url = reverse("login")
        data = {"username": user.username, "password": password}
        response = api_client.post(url, data, HTTP_TENANT_ID=str(tenant.id))
        assert response.status_code == status.HTTP_200_OK

    @patch("accounts.views.authentication_views.login_otp_service.verify", return_value=(True, None))
    def test_verify_login_success(self, mock_otp_verify, api_client, user, tenant, faker):
        url = reverse("verify-login")
        otp = faker.bothify(text="######")
        response = api_client.post(url, {"username": user.username, "otp": otp}, HTTP_TENANT_ID=str(tenant.id))
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data

    @patch("accounts.views.registration_views.email_verification_service.create")
    def test_resend_otp_success(self, mock_email_create, api_client, tenant):
        user = UserFactory(tenant=tenant, is_email_verified=False)
        url = reverse("resend-otp")
        response = api_client.post(url, {"username": user.username}, HTTP_TENANT_ID=str(tenant.id))
        assert response.status_code == status.HTTP_200_OK

    @patch("accounts.views.email_verification_views.email_verification_service.verify", return_value=(True, None))
    def test_verify_email_success(self, mock_email_verify, api_client, tenant, faker):
        user = UserFactory(tenant=tenant, is_email_verified=False)
        url = reverse("verify-email")
        otp = faker.bothify(text="######")
        response = api_client.post(url, {"username": user.username, "otp": otp}, HTTP_TENANT_ID=str(tenant.id))
        assert response.status_code == status.HTTP_201_CREATED

    @patch("accounts.views.password_reset_views.password_reset_service.create")
    def test_forgot_password_success(self, mock_pw_reset_create, api_client, user, tenant):
        url = reverse("forgot-password")
        response = api_client.post(url, {"email": user.email}, HTTP_TENANT_ID=str(tenant.id))
        assert response.status_code == status.HTTP_200_OK

    def test_change_password_success(self, api_client, user, tenant, faker):
        old_password = f"{faker.password(length=10)}A1!"
        new_password = f"{faker.password(length=10)}B2@"
        user.set_password(old_password)
        user.save()
        
        api_client.force_authenticate(user=user)
        url = reverse("change-password")
        data = {
            "current_password": old_password, 
            "new_password": new_password, 
            "confirm_password": new_password
        }
        response = api_client.post(url, data, HTTP_TENANT_ID=str(tenant.id))
        assert response.status_code == status.HTTP_200_OK

    def test_logout_success(self, api_client, user, tenant):
        refresh = RefreshToken.for_user(user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
        url = reverse("logout")
        response = api_client.post(url, {"refresh": str(refresh)}, HTTP_TENANT_ID=str(tenant.id))
        assert response.status_code == status.HTTP_200_OK

    def test_profile_retrieve(self, api_client, user, tenant):
        api_client.force_authenticate(user=user)
        url = reverse("user-detail", kwargs={"id": user.id})
        response = api_client.get(url, HTTP_TENANT_ID=str(tenant.id))
        assert response.status_code == status.HTTP_200_OK

    def test_profile_update(self, api_client, user, tenant, faker):
        api_client.force_authenticate(user=user)
        url = reverse("user-detail", kwargs={"id": user.id})
        new_name = faker.first_name()
        response = api_client.patch(url, {"first_name": new_name}, HTTP_TENANT_ID=str(tenant.id))
        assert response.status_code == status.HTTP_200_OK

    @patch("accounts.views.user_views.blacklist_user_tokens")
    def test_profile_delete(self, mock_blacklist, api_client, user, tenant):
        api_client.force_authenticate(user=user)
        url = reverse("user-detail", kwargs={"id": user.id})
        response = api_client.delete(url, HTTP_TENANT_ID=str(tenant.id))
        assert response.status_code == status.HTTP_204_NO_CONTENT
