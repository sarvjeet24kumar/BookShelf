from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from common.enums import UserRole

User = get_user_model()


class Command(BaseCommand):
    help = "Seed one admin user for the application"

    def handle(self, *args, **options):
        self.stdout.write("Creating admin user...")

        admin_user, created = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@bookshelf.com",
                "first_name": "Admin",
                "last_name": "User",
                "phone_no": "+911234567890",
                "role": UserRole.ADMIN,
                "is_staff": True,
                "is_superuser": True,
            },
        )

        if created:
            admin_user.set_password("admin123")
            admin_user.save()
            self.stdout.write(self.style.SUCCESS("\n✓ Admin user created successfully!"))
            self.stdout.write("\nCredentials:")
            self.stdout.write(f"  Username: admin")
            self.stdout.write(f"  Password: admin123")
            self.stdout.write(f"  Email: admin@bookshelf.com")
            self.stdout.write(f"  First Name: Admin")
            self.stdout.write(f"  Last Name: User")
            self.stdout.write(f"  Phone: +911234567890")
        else:
            self.stdout.write(self.style.WARNING("\n⚠ Admin user already exists"))
            self.stdout.write(f"  Username: {admin_user.username}")
            self.stdout.write(f"  Email: {admin_user.email}")
