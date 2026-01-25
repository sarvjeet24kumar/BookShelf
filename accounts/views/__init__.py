"""
Accounts views package.
- registration_views: User signup
- email_verification_views: Email verification workflow (verify + resend)
- authentication_views: MFA login workflow (login + verify)
- logout_view: Logout functionality
- password_reset_views: Password reset workflow (forgot + reset)
- user_views: User CRUD operations
"""


from accounts.views.registration_views import SignupView


from accounts.views.email_verification_views import (
    VerifyEmailView,
    ResendOTPView,
)


from accounts.views.authentication_views import (
    LoginView,
    VerifyLoginView,
    ResendLoginOTPView,
)


from accounts.views.logout_view import LogoutView


from accounts.views.password_reset_views import (
    ForgotPasswordView,
    ResetPasswordView,
)


from accounts.views.user_views import (
    UserView,
    UserDetailView,
)

__all__ = [

    "SignupView",

    "VerifyEmailView",
    "ResendOTPView",

    "LoginView",
    "VerifyLoginView",
    "ResendLoginOTPView",

    "LogoutView",

    "ForgotPasswordView",
    "ResetPasswordView",

    "UserView",
    "UserDetailView",
]
