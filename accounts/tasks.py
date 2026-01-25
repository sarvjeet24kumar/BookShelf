import logging
from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 10},
)
def send_otp_email(self, email: str, otp: str):
    """
    Send OTP email for email verification with HTML template.
    """
    expiry_minutes = getattr(settings, "OTP_EXPIRY_MINUTES", 15)

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

    logger.info("OTP email sent: email=%s", email)



@shared_task
def cleanup_unverified_users():
    """
    Delete user records that are unverified for more than 24 hours.
    Runs daily to clean up abandoned signups.
    """
    User = get_user_model()
    cutoff_time = timezone.now() - timedelta(hours=24)
    
    # Find unverified users older than 24 hours
    old_unverified_users = User.all_objects.filter(
        is_email_verified=False,
        created_at__lt=cutoff_time
    )
    
    count = old_unverified_users.count()
    
    if count > 0:
        # Hard delete (not soft delete)
        old_unverified_users.delete()
        logger.info(f"Cleaned up {count} unverified users older than 24 hours")
    
    return f"Deleted {count} unverified users"


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 10},
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

This link will expire in {getattr(settings, "OTP_EXPIRY_MINUTES", 15)} minutes.

If you did not request this, please ignore this email.

Thanks,
BookShelf Team
"""
    html_message = render_to_string(
        "accounts/emails/password_reset.html",
        {
            "reset_url": reset_url,
            "expiry_minutes": getattr(settings, "OTP_EXPIRY_MINUTES", 15),
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

    logger.info("Password reset email sent: email=%s", email)
