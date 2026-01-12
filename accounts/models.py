from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinLengthValidator
from common.enums import UserRole
from common.models import BaseModel
from common.validators import (
    username_validator,
    first_name_validator,
    last_name_validator,
    phone_number_validator,
)
from common.constants import (
    MAX_USERNAME_LENGTH,
    MIN_USERNAME_LENGTH,
    MAX_PHONE_LENGTH,
    MAX_ROLE_LENGTH,
    MAX_MAX_LENGTH,
)


class User(AbstractUser, BaseModel):
    username = models.CharField(
        max_length=MAX_USERNAME_LENGTH,
        unique=True,
        validators=[MinLengthValidator(MIN_USERNAME_LENGTH), username_validator],
    )
    email = models.EmailField(unique=True)
    first_name = models.CharField(
        max_length=MAX_MAX_LENGTH, validators=[first_name_validator]
    )
    last_name = models.CharField(
        max_length=MAX_MAX_LENGTH, validators=[last_name_validator]
    )
    phone_no = models.CharField(
        max_length=MAX_PHONE_LENGTH, validators=[phone_number_validator]
    )
    role = models.CharField(
        max_length=MAX_ROLE_LENGTH, choices=UserRole.choices, default=UserRole.USER
    )

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email", "first_name"]

    class Meta:
        db_table = "users"

    def __str__(self):
        return self.username
