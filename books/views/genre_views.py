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
        serializer = GenreSerializer(paginated_queryset, many=True)
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
