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
        default=SubscriptionPlan.FREE
    )

    class Meta:
        db_table = "tenants"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name
    
    def soft_delete(self):
        """
        Override soft_delete to cascade to all tenant-related data.
        
        When a tenant is deleted:
        - Mark tenant as inactive and soft-deleted
        - Cascade soft-delete to all users in this tenant
        - Cascade soft-delete to all books, genres, and related entities
        
        This preserves data for recovery while blocking all access.
        """
    
        
        User = get_user_model()
        now = timezone.now()
        
        self.deleted_at = now
        self.is_active = False
        self.save(update_fields=['deleted_at', 'is_active', 'updated_at'])
        
        User.objects.filter(tenant=self, deleted_at__isnull=True).update(
            deleted_at=now,
            is_active=False,
            updated_at=now
        )
        

        Book.objects.filter(tenant=self, deleted_at__isnull=True).update(
            deleted_at=now,
            updated_at=now
        )
        

        Genre.objects.filter(tenant=self, deleted_at__isnull=True).update(
            deleted_at=now,
            updated_at=now
        )
        

        UserBook.objects.filter(
            book__tenant=self,
            deleted_at__isnull=True
        ).update(deleted_at=now, updated_at=now)
        

        BookGenre.objects.filter(
            book__tenant=self,
            deleted_at__isnull=True
        ).update(deleted_at=now, updated_at=now)
    
    def restore(self):
        """
        Override restore to cascade to all tenant-related data.
        
        When a tenant is restored:
        - Clear tenant's deleted_at and reactivate
        - Cascade restore to all users in this tenant
        - Cascade restore to all books, genres, and related entities
        
        This restores the entire tenant ecosystem.
        """
       
        
        User = get_user_model()
        

        self.deleted_at = None
        self.is_active = True
        self.save(update_fields=['deleted_at', 'is_active', 'updated_at'])
        

        User.all_objects.filter(tenant=self, deleted_at__isnull=False).update(
            deleted_at=None,
            is_active=True,
            updated_at=timezone.now()
        )
        

        Book.all_objects.filter(tenant=self, deleted_at__isnull=False).update(
            deleted_at=None,
            updated_at=timezone.now()
        )
        

        Genre.all_objects.filter(tenant=self, deleted_at__isnull=False).update(
            deleted_at=None,
            updated_at=timezone.now()
        )
        

        UserBook.all_objects.filter(
            book__tenant=self,
            deleted_at__isnull=False
        ).update(deleted_at=None, updated_at=timezone.now())
        

        BookGenre.all_objects.filter(
            book__tenant=self,
            deleted_at__isnull=False
        ).update(deleted_at=None, updated_at=timezone.now())
