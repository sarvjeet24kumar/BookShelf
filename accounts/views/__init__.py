"""
Accounts views package.
- registration_views: User signup
- email_verification_views: Email verification workflow (verify + resend)
- authentication_views: MFA login workflow (login + verify)
- logout_view: Logout functionality
- password_reset_views: Password reset workflow (forgot + reset)
- user_views: User CRUD operations
"""

from .registration_views import SignupView
from .email_verification_views import VerifyEmailView, ResendOTPView
from .authentication_views import LoginView, VerifyLoginView
from .logout_view import LogoutView
from .password_reset_views import ForgotPasswordView, ResetPasswordView
from .change_password_view import ChangePasswordView
from .user_views import (
    UserView,
    UserDetailView,
)

__all__ = [
    "SignupView",
    "VerifyEmailView",
    "ResendOTPView",
    "LoginView",
    "VerifyLoginView",
    "LogoutView",
    "ForgotPasswordView",
    "ResetPasswordView",
    "ChangePasswordView",
    "UserView",
    "UserDetailView",
]
