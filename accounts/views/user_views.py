from rest_framework.generics import ListAPIView, RetrieveDestroyAPIView
from common.permissions import IsAdmin
from rest_framework.pagination import PageNumberPagination
from django.contrib.auth import get_user_model
from accounts.serializers.user_serializers import (
    UserListSerializer,
    UserDetailSerializer,
)
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from common.pagination import CommonPagination


User = get_user_model()


class UserListView(ListAPIView):

    permission_classes = [IsAdmin]
    serializer_class = UserListSerializer
    pagination_class = CommonPagination

    def get_queryset(self):
        queryset = User.objects.filter(role="USER").order_by("-created_at")

        if hasattr(User, "deleted_at"):
            queryset = queryset.filter(deleted_at__isnull=True)

        return queryset


class UserDetailView(RetrieveDestroyAPIView):

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
                {"detail": "User not found or has been deleted."},
                status=status.HTTP_404_NOT_FOUND,
            )

    def destroy(self, request, *args, **kwargs):

        user = self.get_object()
        if user.id == request.user.id:
            return Response(
                {"detail": "You cannot delete your own account."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if user.role == "ADMIN":
            return Response(
                {"detail": "Cannot delete admin users."},
                status=status.HTTP_403_FORBIDDEN,
            )

        user.deleted_at = timezone.now()
        user.is_active = False
        user.save()

        return Response(
            {
                "message": "User deleted successfully.",
            },
            status=status.HTTP_204_NO_CONTENT,
        )
