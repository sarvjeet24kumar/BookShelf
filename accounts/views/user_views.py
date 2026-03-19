import logging
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.contrib.auth import get_user_model
from django.db import transaction
from accounts.serializers.user_serializers import (
    UserSerializer,
    UserDetailSerializer,
)
from common.permissions import IsTenantAdminOrSuperAdmin, IsOwnerOrAdmin
from common.pagination import CommonPagination
from common.enums import UserRole
from accounts.utils.token_utils import blacklist_user_tokens
from accounts.services import email_verification_service

logger = logging.getLogger(__name__)

User = get_user_model()


class UserView(ListCreateAPIView):
    """
    List and create users within tenant.
    """

    permission_classes = [IsTenantAdminOrSuperAdmin]
    pagination_class = CommonPagination
    serializer_class = UserSerializer

    def get_queryset(self):
        if self.request.user.role == UserRole.SUPER_ADMIN:
            return User.all_objects.filter(role=UserRole.ADMIN).order_by("-created_at")

        return User.objects.filter(
            role=UserRole.USER, tenant_id=self.request.user.tenant_id
        ).order_by("-created_at")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data.get("email")

        if request.user.role == UserRole.SUPER_ADMIN:
            role = UserRole.ADMIN
            tenant = serializer.validated_data.get("tenant")

            if not tenant:
                raise ValidationError(
                    {"tenant": "Tenant is required when creating admin users."}
                )

            tenant_id = tenant.id
        else:
            role = UserRole.USER
            tenant = request.user.tenant
            tenant_id = request.user.tenant_id

        if User.all_objects.filter(email=email, tenant_id=tenant_id).exists():
            raise ValidationError("A user with this email already exists.")

        user = serializer.save(
            role=role, tenant=tenant, is_email_verified=False, is_active=False
        )

        email_verification_service.create(
            user.username, user.email, tenant_id=str(tenant_id)
        )

        logger.info("Admin created user successfully")

        return Response(
            {"detail": "Verification code sent to your email."},
            status=status.HTTP_200_OK,
        )


class UserDetailView(RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a user.
    """

    permission_classes = [IsOwnerOrAdmin]
    serializer_class = UserDetailSerializer
    lookup_field = "id"

    def get_queryset(self):
        if self.request.user.role in [UserRole.SUPER_ADMIN, UserRole.ADMIN]:
            return User.all_objects.all()
        return User.objects.all()

    def get_serializer(self, *args, **kwargs):
        exclude_fields = []

        if self.request.user.role == UserRole.USER:
            exclude_fields = ["deleted_at", "is_active"]

        kwargs["exclude_fields"] = exclude_fields
        return super().get_serializer(*args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        """
        Update user account.

        """
        partial = kwargs.pop("partial", False)
        user = self.get_object()
        is_self = user.id == request.user.id

        if "email" in request.data or "role" in request.data:
            logger.warning("Blocked: Attempt to update immutable fields (email/role)")
            raise PermissionDenied("Email and role cannot be changed.")

        if request.user.role == UserRole.ADMIN and not is_self:
            if user.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
                logger.warning(
                    "Blocked: Tenant admin tried to update admin/super admin"
                )
                raise PermissionDenied(
                    "Tenant admin cannot update other admin accounts."
                )

        new_username = request.data.get("username")
        if new_username and new_username.lower() != user.username:
            if User.all_objects.filter(username=new_username.lower()).exists():
                raise ValidationError({"username": "This username is already taken."})

        if request.user.role == UserRole.USER:
            restricted_fields = {"is_active", "deleted_at"}
            if any(field in request.data for field in restricted_fields):
                logger.warning(
                    "Blocked: Regular user tried to update restricted fields"
                )
                raise PermissionDenied(
                    "You cannot update restricted fields (is_active, deleted_at)."
                )

        original_is_active = user.is_active

        serializer = self.get_serializer(user, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        updated_user = serializer.save()

        is_admin = request.user.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]
        if is_admin and original_is_active and not updated_user.is_active:
            blacklist_user_tokens(updated_user)
            logger.info("User suspended and tokens blacklisted")
        else:
            logger.info("User updated successfully")

        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        """
        Delete user account.

        """
        user = self.get_object()
        is_self = user.id == request.user.id
        if request.user.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN] and is_self:
            logger.warning("Blocked: Admin tried to delete self")
            raise PermissionDenied("Admins cannot delete their own account.")

        if request.user.role == UserRole.ADMIN and not is_self:
            if user.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
                logger.warning(
                    "Blocked: Tenant admin tried to delete admin/super admin"
                )
                raise PermissionDenied(
                    "Tenant admin cannot delete other admin or super admin accounts."
                )

        with transaction.atomic():
            if is_self:
                user.soft_delete()
                user.is_active = False
                user.save(update_fields=["is_active"])
                blacklist_user_tokens(user)
                logger.info("User self-deleted and tokens blacklisted")
            else:
                user.soft_delete()
                blacklist_user_tokens(user)
                logger.info("Admin deleted user and blacklisted tokens")

        return Response(status=status.HTTP_204_NO_CONTENT)
