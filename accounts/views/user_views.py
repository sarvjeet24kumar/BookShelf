import logging
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from accounts.serializers.user_serializers import (
    UserSerializer,
    UserDetailSerializer,
    SelfUserSerializer,
)
from common.permissions import IsAdmin
from common.pagination import CommonPagination
from common.enums import UserRole

logger = logging.getLogger(__name__)

User = get_user_model()


class UserView(ListCreateAPIView):

    permission_classes = [IsAdmin]
    pagination_class = CommonPagination
    serializer_class = UserSerializer

    def get_queryset(self):
        queryset = User.objects.filter(role=UserRole.USER).order_by("-created_at")

        if hasattr(User, "deleted_at"):
            queryset = queryset.filter(deleted_at__isnull=True)

        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        logger.info(
            "Admin created user: user_id=%s, created_by=%s", user.id, request.user.id
        )

        return Response(
            {"message": "User created successfully"},
            status=status.HTTP_201_CREATED,
        )


class UserDetailView(RetrieveUpdateDestroyAPIView):

    permission_classes = [IsAdmin]
    serializer_class = UserDetailSerializer
    lookup_field = "id"

    def get_queryset(self):
        return User.objects.filter(deleted_at__isnull=True)

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found or has been deleted."},
                status=status.HTTP_404_NOT_FOUND,
            )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        user = self.get_object()

        if user.role == UserRole.ADMIN:
            logger.warning(
                "Blocked: Admin tried to update admin user: target_id=%s, attempted_by=%s",
                user.id,
                request.user.id,
            )
            return Response(
                {"error": "Cannot update admin users."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = self.get_serializer(user, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        logger.info(
            "Admin updated user: user_id=%s, updated_by=%s", user.id, request.user.id
        )

        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()

        if user.id == request.user.id:
            logger.warning(
                "Blocked: Admin tried to delete self: user_id=%s", request.user.id
            )
            return Response(
                {"error": "You cannot delete your own account."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if user.role == UserRole.ADMIN:
            logger.warning(
                "Blocked: Admin tried to delete admin user: target_id=%s, attempted_by=%s",
                user.id,
                request.user.id,
            )
            return Response(
                {"error": "Cannot delete admin users."},
                status=status.HTTP_403_FORBIDDEN,
            )

        with transaction.atomic():
            user.deleted_at = timezone.now()
            user.is_active = False
            user.save()

            user.user_books.filter(deleted_at__isnull=True).update(
                deleted_at=timezone.now()
            )

        logger.info(
            "User soft-deleted: user_id=%s, deleted_by=%s", user.id, request.user.id
        )

        return Response(status=status.HTTP_204_NO_CONTENT)


class MeAPIView(APIView):

    def get(self, request):
        serializer = SelfUserSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        serializer = SelfUserSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        logger.info("User updated their profile: user_id=%s", request.user.id)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request):
        if request.user.role == UserRole.ADMIN:
            logger.warning(
                "Blocked: Admin tried to self-delete via /me/: user_id=%s",
                request.user.id,
            )
            return Response(
                {"error": "Cannot delete admin users"},
                status=status.HTTP_403_FORBIDDEN,
            )

        with transaction.atomic():
            request.user.deleted_at = timezone.now()
            request.user.is_active = False
            request.user.save()

            request.user.user_books.filter(deleted_at__isnull=True).update(
                deleted_at=timezone.now()
            )

        logger.info("User self-deleted: user_id=%s", request.user.id)

        return Response(status=status.HTTP_204_NO_CONTENT)
