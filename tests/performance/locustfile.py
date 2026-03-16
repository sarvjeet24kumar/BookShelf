import random
from locust import HttpUser, task, between

class BookShelfUser(HttpUser):
    wait_time = between(1, 5)

    @task(3)
    def view_books(self):
        """Simulate a user viewing the book list."""
        self.client.get("/api/v1/books/", name="Get Books")

    @task(1)
    def health_check(self):
        """Simulate a keep-alive health check."""
        self.client.get("/health/", name="Health Check")

    def on_start(self):
        """
        Optional: Define logic to run when a user starts.
        e.g., login or tenant context setup.
        """
        pass
