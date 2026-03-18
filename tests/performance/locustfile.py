import os
import random
from locust import HttpUser, task, between

class BookShelfUser(HttpUser):
    wait_time = between(1, 3)
    host = "http://127.0.0.1:8000"  # Default local host
    tokens_data = []

    def on_start(self):
        """Load tokens and tenants from 'locust_tokens.txt' on start."""
        token_file = "locust_tokens.txt"

        if os.path.exists(token_file):
            with open(token_file, "r") as f:
                for line in f:
                    if ":" in line:
                        parts = line.strip().split(":")
                        if len(parts) == 3:
                            token, slug, user_id = parts
                            self.tokens_data.append({"token": token, "slug": slug, "user_id": user_id})
        
        if not self.tokens_data:
            print("CRITICAL: No valid token:slug:user_id triplets found. Auth tasks will fail.")

    def get_auth_context(self):
        """Helper to get a random auth header + tenant + user_id."""
        if self.tokens_data:
            return random.choice(self.tokens_data)
        return None

    @task(1)
    def api_health_check(self):
        """1. Unauthenticated: Health Check"""
        self.client.get("/health/", name="HealthCheck")

    @task(3)
    def api_user_profile(self):
        """2. Authenticated: User Profile Detail"""
        context = self.get_auth_context()
        if not context: return
        headers = {
            "Authorization": f"Bearer {context['token']}",
            "X-Tenant-Domain": context['slug']
        }
        self.client.get(f"/api/v1/users/{context['user_id']}/", headers=headers, name="UserProfile")

    @task(5)
    def api_list_books(self):
        """3. Authenticated: Book Catalog"""
        context = self.get_auth_context()
        if not context: return
        headers = {
            "Authorization": f"Bearer {context['token']}",
            "X-Tenant-Domain": context['slug']
        }
        self.client.get("/api/v1/books/", headers=headers, name="ListBooks")

    @task(2)
    def api_list_genres(self):
        """4. Authenticated: Genre List"""
        context = self.get_auth_context()
        if not context: return
        headers = {
            "Authorization": f"Bearer {context['token']}",
            "X-Tenant-Domain": context['slug']
        }
        self.client.get("/api/v1/genres/", headers=headers, name="ListGenres")

