from django.urls import path
from accounts.views import (
    SignupView,
    VerifyEmailView,
    ResendOTPView,
    LoginView,
    VerifyLoginView,
    # ResendLoginOTPView,
    LogoutView,
    ForgotPasswordView,
    ResetPasswordView,
    ChangePasswordView,
    UserView,
    UserDetailView,
)
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path("auth/signup/", SignupView.as_view(), name="signup"),
    path("auth/verify-email/", VerifyEmailView.as_view(), name="verify-email"),
    path("auth/resend-otp/", ResendOTPView.as_view(), name="resend-otp"),
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/verify-login/", VerifyLoginView.as_view(), name="verify-login"),
    path("auth/resend-login-otp/", LoginView.as_view(), name="resend-login-otp"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="refresh"),
    path("auth/forgot-password/", ForgotPasswordView.as_view(), name="forgot-password"),
    path("auth/reset-password/", ResetPasswordView.as_view(), name="reset-password"),
    path("auth/change-password/", ChangePasswordView.as_view(), name="change-password"),
    path("users/", UserView.as_view(), name="users"),
    path("users/<uuid:id>/", UserDetailView.as_view(), name="user-detail"),
]
