"""
Custom permissions for multi-tenant access control.
These permissions work with the tenant context set by TenantMiddleware.
"""
from rest_framework.permissions import BasePermission
from common.enums import UserRole, SubscriptionStatus
from payments.models import Subscription


class IsSuperAdmin(BasePermission):
    """
    Permission for Super Admin only.
    Super Admin has tenant=NULL and role=SUPER_ADMIN.
    Used for platform-level operations like managing tenants.
    """
    message = "Super Admin access required."
    
    def has_permission(self, request, view):
        user = request.user
        return (
            user.is_authenticated and
            user.tenant is None and
            user.role == UserRole.SUPER_ADMIN
        )


class IsTenantAdmin(BasePermission):
    """
    Permission for Tenant Admin only.
    Tenant Admin has role=ADMIN within their tenant.
    Used for tenant-level management like managing books/users.
    """
    message = "Tenant Admin access required."
    
    def has_permission(self, request, view):
        user = request.user
        return (
            user.is_authenticated and
            user.tenant is not None and
            user.role == UserRole.ADMIN
        )


class IsTenantMember(BasePermission):
    """
    Permission for any authenticated user within a tenant.
    Used for general tenant user access.
    """
    message = "Tenant member access required."
    
    def has_permission(self, request, view):
        user = request.user
        return (
            user.is_authenticated and
            user.tenant is not None
        )


class IsTenantAdminOrSuperAdmin(BasePermission):
    """
    Permission for Tenant Admin OR Super Admin.
    Used for operations that both admin types can perform.
    """
    message = "Admin access required."
    
    def has_permission(self, request, view):
        user = request.user
        if not user.is_authenticated:
            return False
        
        if user.tenant is None and user.role == UserRole.SUPER_ADMIN:
            return True
        

        if user.tenant is not None and user.role == UserRole.ADMIN:
            return True
        
        return False


class IsOwner(BasePermission):
    """
    Object-level permission for object owner only.
    Requires the object to have a 'user' or 'created_by' field.
    """
    message = "You must be the owner of this object."
    
    def has_object_permission(self, request, view, obj):
        user = request.user
        

        if hasattr(obj, 'user'):
            return obj.user == user
        

        if hasattr(obj, 'created_by'):
            return obj.created_by == user
        
        return False


class IsOwnerOrTenantAdmin(BasePermission):
    """
    Object-level permission for owner OR Tenant Admin.
    Owner can modify their own objects.
    Tenant Admin can modify any object in their tenant.
    """
    message = "You must be the owner or a Tenant Admin."
    
    def has_object_permission(self, request, view, obj):
        user = request.user
        
        if not user.is_authenticated:
            return False
        

        if user.role == UserRole.ADMIN and user.tenant is not None:

            if hasattr(obj, 'tenant'):
                return obj.tenant == user.tenant
            if hasattr(obj, 'user') and hasattr(obj.user, 'tenant'):
                return obj.user.tenant == user.tenant
            return True
        

        if hasattr(obj, 'user'):
            return obj.user == user
        if hasattr(obj, 'created_by'):
            return obj.created_by == user
        
        return False


class IsOwnerOrAdmin(BasePermission):
    """
    Object-level permission for owner OR any Admin (Tenant or Super).
    Used for user-level endpoints where admins can manage any user.
    """
    message = "You must be the owner or an Admin."

    def has_object_permission(self, request, view, obj):
        user = request.user
        
        if not user.is_authenticated:
            return False
            

        if user.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:

            if user.role == UserRole.SUPER_ADMIN:

                if hasattr(obj, 'role'):
                    return obj.role == UserRole.ADMIN
                return False
            
            if user.role == UserRole.ADMIN and user.tenant is not None:

                if hasattr(obj, 'tenant'):
                    return obj.tenant == user.tenant
                if hasattr(obj, 'id') and hasattr(obj, 'tenant'):
                    return obj.tenant == user.tenant

                return False
            

            return False
        

        if hasattr(obj, 'id') and obj.id == user.id: 
            return True
        if hasattr(obj, 'user'):
            return obj.user == user
        if hasattr(obj, 'created_by'):
            return obj.created_by == user
            
        return False


class IsPremiumTenant(BasePermission):
    """
    Permission for users whose tenant has an ACTIVE lifetime subscription.
    Checks the Subscription model as the single source of truth.
    """
    message = "Premium subscription required."

    def has_permission(self, request, view):
        user = request.user
        if not (user.is_authenticated and user.tenant):
            return False


        try:
            return user.tenant.subscription.status == SubscriptionStatus.ACTIVE
        except (AttributeError, Subscription.DoesNotExist):
            return False


class ReadOnly(BasePermission):
    """
    Permission that allows read-only access (GET, HEAD, OPTIONS).
    Used in combination with other permissions.
    """
    message = "Read-only access."
    
    def has_permission(self, request, view):
        return request.method in ('GET', 'HEAD', 'OPTIONS')



class IsAdmin(BasePermission):
    """
    Legacy permission - use IsTenantAdmin instead.
    Checks if user has ADMIN role.
    """
    message = "Admin access required."
    
    def has_permission(self, request, view):
        user = request.user
        return (
            user.is_authenticated and
            user.role == UserRole.ADMIN
        )


class IsUser(BasePermission):
    """
    Legacy permission - use IsTenantMember instead.
    Checks if user has USER role.
    """
    message = "User access required."
    
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role == UserRole.USER
        )
