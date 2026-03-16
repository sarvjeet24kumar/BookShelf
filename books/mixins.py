"""
Mixins for user book views.
"""

from rest_framework.exceptions import NotFound, PermissionDenied
from django.contrib.auth import get_user_model
from common.enums import UserRole

User = get_user_model()


class UserLibraryPermissionMixin:
    """
    Mixin for checking user library access permissions.
    Reusable across views that need to validate library access.
    """

    def check_permission(self, request, user_id):
        """
        Check if request.user has permission to access target user's library.
        Returns target_user if authorized, raises exception otherwise.
        """
        if request.user.tenant is None and request.user.role == UserRole.SUPER_ADMIN:
            raise PermissionDenied("Super Admin cannot access user libraries.")

        if request.user.role == UserRole.ADMIN and request.user.tenant is not None:
            try:
                target_user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                raise NotFound("User not found.")

            if target_user.deleted_at is not None:
                raise NotFound("User not found.")

            if target_user.tenant != request.user.tenant:
                raise NotFound("User not found.")

            return target_user

        if request.user.role == UserRole.USER:
            if str(request.user.id) != str(user_id):
                raise PermissionDenied("You can only access your own library.")
            return request.user
        raise PermissionDenied("Access denied.")
