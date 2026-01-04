from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Users


@admin.register(Users)
class UsersAdmin(BaseUserAdmin):
    list_display = (
        "id",
        "username",
        "email",
        "role",
        "created_at",
    )

    fieldsets = BaseUserAdmin.fieldsets + (
        (
            "Custom Fields",
            {
                "fields": (
                    "role",
                    "created_at",
                    "updated_at",
                    "deleted_at",
                )
            },
        ),
    )

    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (
            "Custom Fields",
            {
                "fields": (
                    "email",
                    "first_name",
                    "last_name",
                    "role",
                )
            },
        ),
    )

    readonly_fields = ("created_at", "updated_at", "deleted_at")
