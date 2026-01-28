import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import NotFound
from common.permissions import IsSuperAdmin
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

    permission_classes = [IsSuperAdmin]

    def get(self, request):
        """List all tenants."""
        tenants = Tenant.all_objects.all().order_by("-created_at")
        serializer = TenantSerializer(tenants, many=True)

        return Response({"count": tenants.count(), "results": serializer.data})

    def post(self, request):
        """Create a new tenant."""
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

    permission_classes = [IsSuperAdmin]

    def get_object(self, id):
        try:
            return Tenant.all_objects.get(id=id)
        except Tenant.DoesNotExist:
            raise NotFound("Tenant not found.")

    def get(self, request, id):
        tenant = self.get_object(id)
        serializer = TenantDetailSerializer(tenant)
        return Response(serializer.data)

    def patch(self, request, id):
        tenant = self.get_object(id)
        serializer = TenantUpdateSerializer(tenant, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        logger.info(
            "Tenant updated: %s by Super Admin %s", tenant.slug, request.user.id
        )

        return Response(TenantDetailSerializer(tenant).data)

    def delete(self, request, id):
        tenant = self.get_object(id)
        tenant.soft_delete()

        logger.info(
            "Tenant deleted: %s by Super Admin %s", tenant.slug, request.user.id
        )

        return Response(status=status.HTTP_204_NO_CONTENT)
