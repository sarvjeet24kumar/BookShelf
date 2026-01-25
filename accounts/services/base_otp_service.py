from abc import ABC, abstractmethod
import logging
from django.core.cache import cache
from django.conf import settings
from accounts.services.otp_generator import hash_otp
from accounts.tasks import send_otp_email

logger = logging.getLogger(__name__)


class BaseOTPService(ABC):
    """
    Abstract base class for OTP services.
    """

    def __init__(self, prefix):
        self.prefix = prefix

    def get_expiry(self):
        return getattr(settings, "OTP_EXPIRY_MINUTES", 5) * 60

    def build_cache_key(self, tenant_id, identifier):
        if tenant_id:
            return f"{self.prefix}:tenant:{tenant_id}:{identifier}"
        return f"{self.prefix}:{identifier}"

    def store_otp(self, identifier, plain_otp, email, tenant_id=None, extra_data=None):
        """Hash OTP, store in cache, and send email. """
        data = {"hashed_otp": hash_otp(plain_otp)}
        if extra_data:
            data.update(extra_data)
        
        cache_key = self.build_cache_key(tenant_id, identifier)
        cache.set(cache_key, data, timeout=self.get_expiry())
        
        self.send_otp_notification(email, plain_otp)

        logger.info(
            "%s OTP created: identifier=%s, tenant=%s",
            self.prefix,
            identifier,
            tenant_id or "None",
        )

    def validate_otp(self, identifier, otp, tenant_id=None):
        """Validate OTP by comparing hashes. Returns (success, error, data)."""
        cache_key = self.build_cache_key(tenant_id, identifier)
        data = cache.get(cache_key)

        if not data:
            return False, "OTP expired. Please request a new one.", None

        if data.get("hashed_otp") != hash_otp(otp):
            return False, "Invalid OTP. Please try again.", None

        return True, "", data

    def delete_otp(self, identifier, tenant_id=None):
        cache_key = self.build_cache_key(tenant_id, identifier)
        cache.delete(cache_key)

    def has_pending(self, identifier, tenant_id=None):
        cache_key = self.build_cache_key(tenant_id, identifier)
        return cache.get(cache_key) is not None

    def cleanup(self, identifier, tenant_id=None):
        self.delete_otp(identifier, tenant_id)

    def send_otp_notification(self, email, otp):
        send_otp_email.delay(email, otp)

    @abstractmethod
    def create(self, *args, **kwargs):
        """Create and send OTP. Must be implemented by subclasses."""
        pass

    @abstractmethod
    def verify(self, *args, **kwargs):
        """Verify OTP. Must be implemented by subclasses."""
        pass
