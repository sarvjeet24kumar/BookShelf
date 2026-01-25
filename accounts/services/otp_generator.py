import secrets
import hashlib
from django.conf import settings


def generate_otp():
    """Generate a random numeric OTP."""
    otp_length = getattr(settings, "OTP_LENGTH", 6)
    return "".join([str(secrets.randbelow(10)) for _ in range(otp_length)])


def hash_otp(otp):
    """Hash OTP using SHA-256 for secure storage."""
    return hashlib.sha256(otp.encode()).hexdigest()
