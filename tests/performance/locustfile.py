import os
import random
from locust import HttpUser, task, between

class BookShelfUser(HttpUser):
    wait_time = between(1, 5)
    host = "http://127.0.0.1:8000"  # Default local host

    def on_start(self):
        """Called when a virtual user starts."""
        self.access_token = os.getenv("LOCUST_ACCESS_TOKEN", "")
        self.tenant = os.getenv("LOCUST_TENANT", "common")
        
        # Set default headers for all subsequent requests
        self.headers = {
            "X-Tenant-Domain": self.tenant
        }
        if self.access_token:
            self.headers["Authorization"] = f"Bearer {self.access_token}"

    @task(3)
    def view_books(self):
        """Simulate a user viewing the book list."""
        self.client.get("/api/v1/books/", headers=self.headers, name="Get Books")

    @task(1)
    def health_check(self):
        """Simulate a keep-alive health check."""
        # Health check usually doesn't need auth or tenant headers
        self.client.get("/health/", name="Health Check")
