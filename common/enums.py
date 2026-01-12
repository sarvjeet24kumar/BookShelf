from django.db import models


class UserRole(models.TextChoices):
    USER = "USER", "User"
    ADMIN = "ADMIN", "Admin"


class BookStatus(models.TextChoices):

    TO_READ = "TO_READ", "To Read"
    READING = "READING", "Reading"
    COMPLETED = "COMPLETED", "Completed"


class RequestStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    APPROVED = "APPROVED", "Approved"
    REJECTED = "REJECTED", "Rejected"


class Visibility(models.TextChoices):
    PUBLIC = "PUBLIC", "Public"
    PRIVATE = "PRIVATE", "Private"
