import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied
from common.permissions import IsSuperAdmin, IsTenantAdminOrSuperAdmin
from common.enums import UserRole
from tenants.models import Tenant
from tenants.serializers.tenant_serializers import (
    TenantSerializer,
    TenantDetailSerializer,
    TenantCreateSerializer,
    TenantUpdateSerializer,
)

logger = logging.getLogger(__name__)


class TenantListCreateView(APIView):
    """
    List all tenants or create a new tenant.

    """

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsSuperAdmin()]
        return [IsTenantAdminOrSuperAdmin()]

    def get(self, request):
        user = request.user

        if user.role == UserRole.SUPER_ADMIN and user.tenant is None:
            tenants = Tenant.all_objects.all().order_by("-created_at")
        else:
            tenants = Tenant.all_objects.filter(id=user.tenant_id)

        serializer = TenantSerializer(tenants, many=True)
        return Response({"count": tenants.count(), "results": serializer.data})

    def post(self, request):
        serializer = TenantCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        tenant = serializer.save()

        logger.info(
            "Tenant created: %s by Super Admin %s", tenant.slug, request.user.id
        )

        return Response(TenantSerializer(tenant).data, status=status.HTTP_201_CREATED)


class TenantDetailView(APIView):
    """
    Retrieve, update, or delete a tenant.

    """

    def get_permissions(self):
        if self.request.method in ["PATCH", "DELETE"]:
            return [IsSuperAdmin()]
        return [IsTenantAdminOrSuperAdmin()]

    def get_object(self, request, id):
        user = request.user

        try:
            tenant = Tenant.all_objects.get(id=id)
        except Tenant.DoesNotExist:
            raise NotFound("Tenant not found.")

        # Tenant Admin can only access their own tenant
        if user.role == UserRole.ADMIN and user.tenant is not None:
            if tenant.id != user.tenant_id:
                raise PermissionDenied("You can only access your own tenant.")

        return tenant

    def get(self, request, id):
        tenant = self.get_object(request, id)
        serializer = TenantDetailSerializer(tenant)
        return Response(serializer.data)

    def patch(self, request, id):
        tenant = self.get_object(request, id)
        serializer = TenantUpdateSerializer(tenant, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        logger.info(
            "Tenant updated: %s by Super Admin %s", tenant.slug, request.user.id
        )

        return Response(TenantDetailSerializer(tenant).data)

    def delete(self, request, id):
        tenant = self.get_object(request, id)
        tenant.soft_delete()

        logger.info(
            "Tenant deleted: %s by Super Admin %s", tenant.slug, request.user.id
        )

        return Response(status=status.HTTP_204_NO_CONTENT)
