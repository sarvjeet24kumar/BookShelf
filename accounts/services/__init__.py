"""
OTP and authentication services.

Professional interface-based architecture following SOLID principles.
Each service has a single responsibility and inherits from a common base.
"""

from accounts.services.email_verification_service import EmailVerificationOTPService
from accounts.services.login_otp_service import LoginOTPService
from accounts.services.password_reset_service import PasswordResetTokenService

# Service instances (singletons)
email_verification_service = EmailVerificationOTPService()
login_otp_service = LoginOTPService()
password_reset_service = PasswordResetTokenService()

__all__ = [
    "email_verification_service",
    "login_otp_service",
    "password_reset_service",
    "EmailVerificationOTPService",
    "LoginOTPService",
    "PasswordResetTokenService",
]
