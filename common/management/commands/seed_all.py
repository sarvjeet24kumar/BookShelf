from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Seed everything: admin user, books, and genres"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("=" * 50))
        self.stdout.write(self.style.SUCCESS("Starting complete database seeding..."))
        self.stdout.write(self.style.SUCCESS("=" * 50))
        self.stdout.write("")

        # Step 1: Seed admin user
        self.stdout.write(self.style.HTTP_INFO("Step 1/2: Seeding admin user"))
        call_command("seed_admin")

        self.stdout.write("")

        # Step 2: Seed books and genres
        self.stdout.write(self.style.HTTP_INFO("Step 2/2: Seeding books and genres"))
        call_command("seed")

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 50))
        self.stdout.write(self.style.SUCCESS("✓ All seeding completed successfully!"))
        self.stdout.write(self.style.SUCCESS("=" * 50))
