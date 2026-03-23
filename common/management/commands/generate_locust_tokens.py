from django.core.management.base import BaseCommand
from accounts.models import User
from rest_framework_simplejwt.tokens import RefreshToken

class Command(BaseCommand):
    help = "Generates JWT access tokens for verified users with active tenants for Locust testing."

    def handle(self, *args, **options):
        token_file = "locust_tokens.txt"
        users = User.objects.filter(
            is_active=True, 
            is_email_verified=True,
            tenant__isnull=False,
            tenant__is_active=True
        ).select_related('tenant')[:10]
        
        if not users.exists():
            self.stdout.write(self.style.ERROR(" Error: No active, verified users with tenants found."))
            return

        lines = []
        for user in users:
            refresh = RefreshToken.for_user(user)
            token = str(refresh.access_token)
            slug = user.tenant.slug
            user_id = str(user.id)
            lines.append(f"{token}:{slug}:{user_id}")
        
        with open(token_file, "w") as f:
            for line in lines:
                f.write(f"{line}\n")
                
        self.stdout.write(self.style.SUCCESS(f" Success: Generated tokens for {len(lines)} verified users in '{token_file}'"))
