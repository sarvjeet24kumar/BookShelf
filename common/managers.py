from django.db import models
from django.contrib.auth.models import UserManager
from common.enums import UserRole
from tenants.context import get_current_tenant


class SoftDeleteManager(models.Manager):
    """
    Manager that auto-excludes soft-deleted records.

    """

    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)


class TenantAwareManager(SoftDeleteManager):
    """
    Manager that auto-filters by current tenant AND excludes soft-deleted.
    Inherits SoftDeleteManager for deleted_at filtering.

    """

    def get_queryset(self):

        queryset = super().get_queryset()
        tenant = get_current_tenant()

        if tenant:
            return queryset.filter(tenant=tenant)
        return queryset


class TenantAwareAllObjectsManager(models.Manager):
    """
    Manager that filters by current tenant but INCLUDES soft-deleted records.
    Used for admin operations within a tenant (e.g., restore deleted items).

    """

    def get_queryset(self):

        queryset = super().get_queryset()
        tenant = get_current_tenant()

        if tenant:
            return queryset.filter(tenant=tenant)
        return queryset


class TenantAwareUserManager(UserManager):
    def get_queryset(self):
        queryset = super().get_queryset().filter(deleted_at__isnull=True)
        tenant = get_current_tenant()
        if tenant:
            return queryset.filter(tenant=tenant)
        return queryset

    def _create_user(self, username, email, password, **extra_fields):
        """Override to ensure email is normalized."""
        if not username:
            raise ValueError("Username is required")
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(username, email, password, **extra_fields)

    def create_superuser(self, username, email=None, password=None, **extra_fields):

        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_email_verified", True)
        extra_fields.setdefault("role", UserRole.SUPER_ADMIN)
        return self._create_user(username, email, password, **extra_fields)
