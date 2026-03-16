import logging
from accounts.services.base_otp_service import BaseOTPService
from accounts.services.otp_generator import generate_otp

logger = logging.getLogger(__name__)


class LoginOTPService(BaseOTPService):
    """OTP service for MFA login. Uses username as identifier."""

    def __init__(self):
        super().__init__(prefix="login")

    def create(self, username, email, tenant_id=None):
        """Create and send login OTP."""
        plain_otp = generate_otp()
        self.store_otp(username, plain_otp, email, tenant_id=tenant_id)

    def verify(self, username, otp, tenant_id=None):
        """Verify OTP. Returns (success, error)."""
        success, error, _ = self.validate_otp(username, otp, tenant_id=tenant_id)

        if not success:
            return False, "OTP expired or invalid. Please request a new one."

        return True, ""
