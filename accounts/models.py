from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinLengthValidator
from common.enums import UserRole
from common.models import BaseModel
from common.managers import TenantAwareUserManager
from common.validators import (
    username_validator,
    first_name_validator,
    last_name_validator,
    phone_number_validator,
)
from accounts.constants import (
    MAX_USERNAME_LENGTH,
    MIN_USERNAME_LENGTH,
    MAX_PHONE_LENGTH,
    MAX_ROLE_LENGTH,
    MAX_NAME_LENGTH,
)


class User(AbstractUser, BaseModel):
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='users'
    )
    
    # Use TenantAwareUserManager for proper create_user/create_superuser support
    objects = TenantAwareUserManager()
    all_objects = models.Manager()
    username = models.CharField(
        max_length=MAX_USERNAME_LENGTH,
        unique=True,
        validators=[MinLengthValidator(MIN_USERNAME_LENGTH), username_validator],
    )
    email = models.EmailField()
    first_name = models.CharField(
        max_length=MAX_NAME_LENGTH, validators=[first_name_validator]
    )
    last_name = models.CharField(
        max_length=MAX_NAME_LENGTH, validators=[last_name_validator]
    )
    phone_no = models.CharField(
        max_length=MAX_PHONE_LENGTH, validators=[phone_number_validator]
    )
    role = models.CharField(
        max_length=MAX_ROLE_LENGTH, choices=UserRole.choices, default=UserRole.USER
    )
    is_email_verified = models.BooleanField(
        default=False
    )

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email", "first_name"]

    class Meta:
        db_table = "user"
        unique_together = [('email', 'tenant')]

    def __str__(self):
        return self.username
