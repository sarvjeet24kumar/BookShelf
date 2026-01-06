from django.db import models


class UserRole(models.TextChoices):
    USER = "USER", "User"
    ADMIN = "ADMIN", "Admin"


class BookStatus(models.TextChoices):

    TO_READ = "TO_READ", "To Read"
    READING = "READING", "Reading"
    COMPLETED = "COMPLETED", "Completed"
