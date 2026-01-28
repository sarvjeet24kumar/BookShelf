"""
Views for Genre management.
Uses TenantAwareManager for automatic tenant filtering.
"""

import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from books.models import Genre
from books.serializers import GenreSerializer
from common.pagination import CommonPagination
from common.enums import UserRole
from common.permissions import IsTenantMember, IsTenantAdmin
from rest_framework.exceptions import NotFound

logger = logging.getLogger(__name__)


class GenreListView(APIView):
    """
    List and create genres.
    """

    permission_classes = [IsTenantMember]

    def get(self, request):
        if request.user.role == UserRole.ADMIN:
            queryset = Genre.all_objects.all().order_by("name")
        else:
            queryset = Genre.objects.all().order_by("name")

        paginator = CommonPagination()
        paginated_queryset = paginator.paginate_queryset(queryset, request)

    def get(self, request):
        if request.user.role == UserRole.ADMIN:
            queryset = Genre.all_objects.all().order_by("name")
        else:
            queryset = Genre.objects.all().order_by("name")

        paginator = CommonPagination()
        paginated_queryset = paginator.paginate_queryset(queryset, request)

        exclude_fields = []
        if request.user.role != UserRole.ADMIN:
            exclude_fields.append("deleted_at")

        serializer = GenreSerializer(
            paginated_queryset,
            many=True,
            exclude_fields=exclude_fields,
        )
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        if request.user.role != UserRole.ADMIN:
            raise PermissionDenied("Only admins can create genres.")

        serializer = GenreSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        genre = serializer.save(tenant=request.user.tenant)

        logger.info(
            "Genre created: genre_id=%s, name=%s, created_by=%s",
            genre.id,
            genre.name,
            request.user.id,
        )

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class GenreDetailView(APIView):
    """
    Retrieve, update, or delete a genre.
    """

    permission_classes = [IsTenantMember]

    def get_object(self, id):
        """Get genre by ID with tenant filtering."""
        try:
            if self.request.user.role == UserRole.ADMIN:
                return Genre.all_objects.get(id=id, tenant=self.request.user.tenant)
            else:
                return Genre.objects.get(id=id)
        except Genre.DoesNotExist:
            return None

    def get(self, request, id):
        """Retrieve genre details."""
        genre = self.get_object(id)
        if not genre:
            raise NotFound("Genre not found.")
        exclude_fields = []
        if request.user.role != UserRole.ADMIN:
            exclude_fields.append("deleted_at")

        serializer = GenreSerializer(
            genre,
            exclude_fields=exclude_fields,
        )
        return Response(serializer.data)

    def patch(self, request, id):
        """Update genre (admin only)."""
        if request.user.role != UserRole.ADMIN:
            raise PermissionDenied("Only admins can update genres.")

        genre = self.get_object(id)
        if not genre:
            raise NotFound("Genre not found.")

        serializer = GenreSerializer(
            genre, data=request.data, context={"request": request}, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        logger.info(
            "Genre updated: genre_id=%s, name=%s, updated_by=%s",
            genre.id,
            genre.name,
            request.user.id,
        )

        return Response(serializer.data)

    def delete(self, request, id):
        """Soft delete genre (admin only)."""
        if request.user.role != UserRole.ADMIN:
            raise PermissionDenied("Only admins can delete genres.")

        genre = self.get_object(id)
        if not genre:
            raise NotFound("Genre not found.")

        genre.delete()

        logger.info(
            "Genre deleted: genre_id=%s, name=%s, deleted_by=%s",
            genre.id,
            genre.name,
            request.user.id,
        )

        return Response(
            {"detail": "Genre deleted successfully."}, status=status.HTTP_204_NO_CONTENT
        )
