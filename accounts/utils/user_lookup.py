from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError
from common.enums import UserRole

User = get_user_model()


def validate_email_or_username(email, username):
    """
    Validate that exactly one of email or username is provided.
    """
    if email and username:
        raise ValidationError("Provide either email or username, not both.")
    if not email and not username:
        raise ValidationError("Email or username is required.")


def find_user(email=None, username=None, tenant=None):
    """
    Find user by email or username with optional tenant filtering.
    """
    tenant_id = tenant.id if tenant else None

    if username:
        if tenant_id is not None:
            return User.all_objects.filter(username=username, tenant_id=tenant_id).first()
        else:
            return User.all_objects.filter(username=username, tenant_id__isnull=True,role=UserRole.SUPER_ADMIN).first()
    
    if email:
        if tenant_id is not None:
            return User.all_objects.filter(email=email, tenant_id=tenant_id).first()
        else:
            return User.all_objects.filter(email=email, tenant_id__isnull=True,role=UserRole.SUPER_ADMIN).first()
    
    return None


def find_user_with_validation(email, username, tenant, require_otp=False, otp=None):
    """
    Validate input and find user in one step.
    """
    validate_email_or_username(email, username)
    
    if require_otp and not otp:
        raise ValidationError("OTP is required.")
    
    return find_user(email=email, username=username, tenant=tenant)
