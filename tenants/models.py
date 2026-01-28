from django.db import models
from django.utils import timezone
from common.models import BaseModel
from common.enums import SubscriptionPlan
from tenants.constants import (
    MAX_TENANT_NAME_LENGTH,
    MAX_TENANT_SLUG_LENGTH,
    MAX_SUBSCRIPTION_PLAN_LENGTH,
)
from django.contrib.auth import get_user_model
from books.models import Book, Genre, UserBook, BookGenre


class Tenant(BaseModel):

    name = models.CharField(max_length=MAX_TENANT_NAME_LENGTH)
    slug = models.SlugField(max_length=MAX_TENANT_SLUG_LENGTH, unique=True)
    is_active = models.BooleanField(default=True)
    subscription_plan = models.CharField(
        max_length=MAX_SUBSCRIPTION_PLAN_LENGTH,
        choices=SubscriptionPlan.choices,
        default=SubscriptionPlan.FREE,
    )

    class Meta:
        db_table = "tenants"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name
