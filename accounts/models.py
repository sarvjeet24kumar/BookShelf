from django.contrib.auth.models import AbstractUser
from django.db import models
from common.enums import UserRole
from common.constants import (
    MAX_USERNAME_LENGTH,
    MAX_EMAIL_LENGTH,
    MAX_NAME_LENGTH,
    MAX_PHONE_LENGTH,
)
from common.models import BaseModel


class Users(AbstractUser, BaseModel):
    username = models.CharField(
        max_length=MAX_USERNAME_LENGTH, unique=True, blank=False, null=False
    )
    email = models.EmailField(
        max_length=MAX_EMAIL_LENGTH, unique=True, blank=False, null=False
    )
    first_name = models.CharField(max_length=MAX_NAME_LENGTH, blank=False, null=False)
    last_name = models.CharField(max_length=MAX_NAME_LENGTH, blank=True, null=True)
    phone_no = models.CharField(max_length=MAX_PHONE_LENGTH, blank=False, null=False)
    role = models.CharField(
        max_length=10, choices=UserRole.choices, default=UserRole.USER
    )
    deleted_at = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email", "first_name"]

    class Meta:
        db_table = "users"

    def __str__(self):
        return self.username
