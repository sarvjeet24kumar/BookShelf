"""
Base model with soft delete support and custom managers.
All models should inherit from BaseModel or TenantAwareModel.
"""
import uuid6
from django.db import models
from django.utils import timezone
from common.managers import SoftDeleteManager, TenantAwareManager, TenantAwareAllObjectsManager


class BaseModel(models.Model):
    """
    Abstract base model with UUID primary key, timestamps, and soft delete.
    
    Managers:
        objects -     Default, excludes soft-deleted records
        all_object-  Includes soft-deleted records (for admin/restore)
    
    Methods:
        soft_delete()-  Set deleted_at to now
        restore()-      Clear deleted_at
    """
    
    id = models.UUIDField(primary_key=True, default=uuid6.uuid7, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    

    objects = SoftDeleteManager()
    

    all_objects = models.Manager()
    
    class Meta:
        abstract = True
    
    def soft_delete(self):
        """Soft delete this record by setting deleted_at."""
        self.deleted_at = timezone.now()
        self.save(update_fields=['deleted_at', 'updated_at'])
    
    def restore(self):
        """Restore a soft-deleted record by clearing deleted_at."""
        self.deleted_at = None
        self.save(update_fields=['deleted_at', 'updated_at'])
    
    @property
    def is_deleted(self):
        """Check if this record is soft-deleted."""
        return self.deleted_at is not None


class TenantAwareModel(BaseModel):
    """
    Abstract model for tenant-scoped models.
    Extends BaseModel with tenant FK and auto filtering.
    
    Managers:
        objects-  Default, auto-filters by tenant + excludes soft-deleted
        all_objects - Includes all records (for admin/restore operations)
    
    Models extending this will:
    - Have tenant FK automatically
    - Use TenantAwareManager (auto-filters by tenant + soft delete)
    """
    
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='%(class)ss'
    )
    
    
    objects = TenantAwareManager()
    

    all_objects = TenantAwareAllObjectsManager()
    
    class Meta:
        abstract = True

