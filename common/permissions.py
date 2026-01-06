from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied


class IsAdmin(BasePermission):

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if not hasattr(request.user, "role"):
            raise PermissionDenied("User role not found.")

        if request.user.role != "ADMIN":
            raise PermissionDenied("Only admins can access this resource.")

        return True


class IsUser(BasePermission):
    message = "Only users are allowed to access this endpoint."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "USER"
        )
