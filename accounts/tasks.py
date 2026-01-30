import logging
from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.cache import cache
from common.constants import (
    CELERY_MAX_RETRIES,
    CELERY_COUNTDOWN_SHORT,
    CELERY_COUNTDOWN_LONG,
    TENANT_SEED_CACHE_TTL,
    DEFAULT_OTP_EXPIRY_MINUTES,
    DEFAULT_USER_DATA_RETENTION_DAYS,
    DEFAULT_UNVERIFIED_USER_CLEANUP_HOURS,
)

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={
        "max_retries": CELERY_MAX_RETRIES,
        "countdown": CELERY_COUNTDOWN_SHORT,
    },
)
def send_otp_email(self, email: str, otp: str):
    """
    Send OTP email for email verification with HTML template.
    """
    expiry_minutes = getattr(settings, "OTP_EXPIRY_MINUTES", DEFAULT_OTP_EXPIRY_MINUTES)

    subject = "BookShelf - Security Verification Code"

    text_message = f"""
Hi,

Your security verification code is: {otp}

This code is valid for {expiry_minutes} minutes.

If you did not request this, please ignore this email.

Thanks,
BookShelf Team
"""

    html_message = render_to_string(
        "accounts/emails/otp_verification.html",
        {"otp": otp, "expiry_minutes": expiry_minutes},
    )

    email_message = EmailMultiAlternatives(
        subject=subject,
        body=text_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[email],
    )
    email_message.attach_alternative(html_message, "text/html")
    email_message.send(fail_silently=False)

    logger.info("Login OTP sent successfully")


@shared_task
def cleanup_unverified_users():
    """
    Delete user records that are unverified for more than 24 hours.
    """
    User = get_user_model()
    cutoff_time = timezone.now() - timedelta(
        hours=DEFAULT_UNVERIFIED_USER_CLEANUP_HOURS
    )

    # Find unverified users older than 24 hours
    old_unverified_users = User.all_objects.filter(
        is_email_verified=False, created_at__lt=cutoff_time
    )

    count = old_unverified_users.count()

    if count > 0:
        old_unverified_users.delete()
        logger.info(f"Cleaned up {count} unverified users older than 24 hours")

    return f"Deleted {count} unverified users"


@shared_task
def cleanup_deleted_users_data():
    """
    Permanently delete  user data (reading lists/UserBooks) for users
    who have been soft-deleted for longer than the retention period.
    """
    User = get_user_model()
    retention_days = getattr(
        settings, "USER_DATA_RETENTION_DAYS", DEFAULT_USER_DATA_RETENTION_DAYS
    )
    cutoff_time = timezone.now() - timedelta(days=retention_days)

    users_to_purge = User.all_objects.filter(deleted_at__lt=cutoff_time)

    total_purged = 0
    for user in users_to_purge:
        purged_count = user.user_books.all().delete()[0]
        if purged_count > 0:
            total_purged += purged_count
            logger.info(f"Purged {purged_count} records for soft-deleted user")

    return f"Purged data for {users_to_purge.count()} users, total records deleted: {total_purged}"


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={
        "max_retries": CELERY_MAX_RETRIES,
        "countdown": CELERY_COUNTDOWN_SHORT,
    },
)
def send_password_reset_email(self, email: str, token: str):
    """
    Send password reset link email with HTML template.
    """
    reset_url = f"{settings.SITE_URL}/api/v1/auth/reset-password/?token={token}"

    subject = "BookShelf - Reset Your Password"

    text_message = f"""
Hi,

Please use the link below to reset your password:
{reset_url}

This link will expire in {getattr(settings, "OTP_EXPIRY_MINUTES", DEFAULT_OTP_EXPIRY_MINUTES)} minutes.

If you did not request this, please ignore this email.

Thanks,
BookShelf Team
"""
    html_message = render_to_string(
        "accounts/emails/password_reset.html",
        {
            "reset_url": reset_url,
            "expiry_minutes": getattr(
                settings, "OTP_EXPIRY_MINUTES", DEFAULT_OTP_EXPIRY_MINUTES
            ),
        },
    )

    email_message = EmailMultiAlternatives(
        subject=subject,
        body=text_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[email],
    )
    email_message.attach_alternative(html_message, "text/html")
    email_message.send(fail_silently=False)

    logger.info("Password reset email sent successfully")


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={
        "max_retries": CELERY_MAX_RETRIES,
        "countdown": CELERY_COUNTDOWN_LONG,
    },
)
def seed_tenant_task(self, tenant_id: str, admin_user_id: str):
    """
    Asynchronous task to seed a new tenant with initial data.
    """

    cache_key = f"tenant_seeded:{tenant_id}"

    if cache.get(cache_key):
        logger.info("Tenant already seeded, skipping task.")
        return "Tenant already seeded"

    logger.info("Executing Celery task: Seeding tenant")

    try:
        call_command("seed", tenant_id=tenant_id, admin_user_id=admin_user_id)
        cache.set(cache_key, True, timeout=TENANT_SEED_CACHE_TTL)
        logger.info("Successfully seeded tenant")
        return "Successfully seeded tenant"

    except Exception as e:
        logger.error(f"Error seeding tenant: {str(e)}")
        raise e
