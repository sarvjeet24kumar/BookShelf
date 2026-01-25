from accounts.services.base_otp_service import BaseOTPService
from accounts.services.otp_generator import generate_otp


class EmailVerificationOTPService(BaseOTPService):
    """OTP service for email verification. Uses username as identifier."""
    
    def __init__(self):
        super().__init__(prefix="verify")

    def create(self, username, email, tenant_id=None):
        """Create and send verification OTP."""
        plain_otp = generate_otp()
        self.store_otp(username, plain_otp, email, tenant_id=tenant_id)
    
    def verify(self, username, otp, tenant_id=None):
        """Verify OTP. Returns (success, error)."""
        success, error, _ = self.validate_otp(username, otp, tenant_id)
        return success, error
