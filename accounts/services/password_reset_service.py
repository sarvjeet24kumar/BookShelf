import uuid
import logging
from accounts.services.base_otp_service import BaseOTPService
from accounts.tasks import send_password_reset_email

logger = logging.getLogger(__name__)


class PasswordResetTokenService(BaseOTPService):
    """Service for password reset tokens. Uses UUID tokens (globally unique)."""
    
    def __init__(self):
        super().__init__(prefix="password_reset")
    
    def build_cache_key(self, tenant_id, identifier):
        """Override: Password reset uses token directly as cache key.
        Token is UUID (globally unique), so no tenant_id needed.
        """
        return f"{self.prefix}:{identifier}"
    
    def send_otp_notification(self, email, token):
        """Override: Send password reset email instead of OTP."""
        send_password_reset_email.delay(email, token)
    
    def create(self, username, user_id, email, tenant_id=None):
        """Create and send password reset token. Stores user_id (needed for reset)."""
        token = str(uuid.uuid4())
        self.store_otp(token, token, email, tenant_id=None, extra_data={"user_id": str(user_id)})
        
        logger.info("Password reset token created: username=%s", username)
        return token
    
    def verify(self, token):
        """Verify password reset token. Returns (success, error, user_id)."""
        success, error, data = self.validate_otp(token, token, tenant_id=None)
        
        if not success:
            return False, "Reset link expired or invalid. Please request a new one.", None
        
        return True, "", data.get("user_id")
    
    def cleanup(self, token):
        """Clean up password reset token."""
        return super().cleanup(token, tenant_id=None)
