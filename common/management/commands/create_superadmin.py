"""
Django management command to create global superadmin.

Usage:
    python manage.py create_superadmin

Environment Variables:
    SUPERADMIN_USERNAME (default: 'superadmin')
    SUPERADMIN_EMAIL (default: 'admin@bookshelf.com')
    SUPERADMIN_PASSWORD (required)
    SUPERADMIN_FIRST_NAME (default: 'Super')
    SUPERADMIN_LAST_NAME (default: 'Admin')
    SUPERADMIN_PHONE (default: '0000000000')

Features:
    - Idempotent (safe to run multiple times)
    - Environment-based credentials
    - Creates global admin (tenant=None)
"""

import environ
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model

User = get_user_model()

# Initialize environ
env = environ.Env()


class Command(BaseCommand):

    def handle(self, *args, **options):
        username = env.str("SUPERADMIN_USERNAME", default="superadmin")
        email = env.str("SUPERADMIN_EMAIL", default="admin@bookshelf.com")
        password = env.str("SUPERADMIN_PASSWORD", default=None)
        first_name = env.str("SUPERADMIN_FIRST_NAME", default="Super")
        last_name = env.str("SUPERADMIN_LAST_NAME", default="Admin")
        phone_no = env.str("SUPERADMIN_PHONE", default="0000000000")

        if not password:
            raise CommandError("SUPERADMIN_PASSWORD environment variable is required.")

        if User.all_objects.filter(username=username).exists():
            self.stdout.write(
                self.style.WARNING(
                    f'Superadmin "{username}" already exists - skipping creation'
                )
            )
            return

        try:
            superadmin = User.objects.create_superuser(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                phone_no=phone_no,
                tenant=None,
            )

            self.stdout.write(
                self.style.SUCCESS(f'Superadmin "{username}" created successfully')
            )
            self.stdout.write(f"Email: {email}")
            self.stdout.write(f"ID: {superadmin.id}")

        except Exception as e:
            raise CommandError(f"Failed to create superadmin: {str(e)}")
