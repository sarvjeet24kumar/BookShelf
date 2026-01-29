from django.db import models


class UserRole(models.TextChoices):
    USER = "USER", "User"
    ADMIN = "ADMIN", "Admin"
    SUPER_ADMIN = "SUPER_ADMIN", "Super Admin"


class BookStatus(models.TextChoices):

    TO_READ = "TO_READ", "To Read"
    READING = "READING", "Reading"
    COMPLETED = "COMPLETED", "Completed"


class RequestStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    APPROVED = "APPROVED", "Approved"
    REJECTED = "REJECTED", "Rejected"



class SubscriptionPlan(models.TextChoices):
    FREE = "FREE", "Free"
    PREMIUM = "PREMIUM", "Premium"


class SubscriptionStatus(models.TextChoices):
    CREATED = "CREATED", "Created"
    ACTIVE = "ACTIVE", "Active"
    CANCELLED = "CANCELLED", "Cancelled"


class PaymentStatus(models.TextChoices):
    CREATED = "CREATED", "Created"
    PAID = "PAID", "Paid"
    VERIFIED = "VERIFIED", "Verified"
    FAILED = "FAILED", "Failed"
    ACTIVATED = "ACTIVATED", "Activated"


class RazorpayOrderStatus(models.TextChoices):
    CREATED = "created", "Created"
    ATTEMPTED = "attempted", "Attempted"
    PAID = "paid", "Paid"


class RazorpayPaymentStatus(models.TextChoices):
    CREATED = "created", "Created"
    AUTHORIZED = "authorized", "Authorized"
    CAPTURED = "captured", "Captured"
    REFUNDED = "refunded", "Refunded"
    FAILED = "failed", "Failed"
