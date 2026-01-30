import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import NotFound, ValidationError
from django.contrib.auth import get_user_model
from books.models import Book, UserBook
from books.serializers import (
    UserBookListSerializer,
    UserBookAddSerializer,
    UserBookUpdateSerializer,
)
from books.filters import MyBookFilter
from books.constants import FREE_PLAN_BOOK_LIMIT
from books.mixins import UserLibraryPermissionMixin
from common.pagination import CommonPagination
from common.enums import BookStatus, RequestStatus, UserRole, SubscriptionPlan
from common.permissions import IsTenantMember

logger = logging.getLogger(__name__)

User = get_user_model()


class UserBooksView(UserLibraryPermissionMixin, APIView):
    """
    List user's books and add books to library.
    """

    permission_classes = [IsTenantMember]



    def get(self, request, user_id):
        """List all books in a user's library."""
        target_user = self.check_permission(request, user_id)

        queryset = (
            Book.objects.filter(
                user_books__user=target_user,
                user_books__deleted_at__isnull=True,
            )
            .distinct()
            .prefetch_related("book_genres__genre")
        )

        filterset = MyBookFilter(request.query_params, queryset=queryset)
        queryset = filterset.qs

        paginator = CommonPagination()
        paginated_queryset = paginator.paginate_queryset(queryset, request)

        serializer_context = {"request": request, "target_user": target_user}
        serializer = UserBookListSerializer(
            paginated_queryset,
            many=True,
            context=serializer_context,
        )

        return paginator.get_paginated_response(serializer.data)

    def post(self, request, user_id):
        """Add a book to user's library."""
        target_user = self.check_permission(request, user_id)

        serializer = UserBookAddSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        book_id = serializer.validated_data["book_id"]
        status_value = serializer.validated_data["status"]
        try:
            book = Book.objects.get(id=book_id)
        except Book.DoesNotExist:
            raise NotFound("Book not available or deleted.")

        if book.request_status != RequestStatus.APPROVED:
            raise ValidationError(
                f"Only APPROVED books can be added. This book is {book.request_status}."
            )

        user_book = UserBook.all_objects.filter(user=target_user, book=book).first()

        if user_book:
            if user_book.deleted_at:
                if target_user.tenant.subscription_plan == SubscriptionPlan.FREE:
                    current_count = UserBook.objects.filter(user=target_user).count()
                    if current_count > FREE_PLAN_BOOK_LIMIT:
                        raise ValidationError(
                            f"Free plan limit reached ({FREE_PLAN_BOOK_LIMIT} books). "
                            "Upgrade to Premium to add more books!"
                        )
                user_book.restore()
                user_book.status = status_value
                user_book.save(update_fields=["status", "updated_at"])
                logger.info(
                    "Book restored to library"
                )
                return Response(
                    {"detail": "Book added to library."},
                    status=status.HTTP_201_CREATED,
                )
            else:
                raise ValidationError("Book already in library.")

        if target_user.tenant.subscription_plan == SubscriptionPlan.FREE:
            current_count = UserBook.objects.filter(user=target_user).count()
            if current_count > FREE_PLAN_BOOK_LIMIT:
                raise ValidationError(
                    f"Free plan limit reached ({FREE_PLAN_BOOK_LIMIT} books). "
                    "Upgrade to Premium for unlimited books!"
                )

        UserBook.objects.create(user=target_user, book=book, status=status_value)

        logger.info(
            "Book added to library"
        )

        return Response(
            {"detail": "Book added to library."},
            status=status.HTTP_201_CREATED,
        )


class UserBookDetailView(UserLibraryPermissionMixin, APIView):
    """
    Retrieve, update, or delete a book from user's library.
    """

    permission_classes = [IsTenantMember]



    def get_object(self, request, user_id, book_id):
        """Get user's book by ID or raise NotFound exception."""
        target_user = self.check_permission(request, user_id)

        user_book = UserBook.objects.filter(
            user=target_user,
            book_id=book_id,
        ).first()

        if not user_book:
            raise NotFound("Book not found in library.")

        return user_book, target_user

    def get(self, request, user_id, book_id):
        """Get details of a specific book in user's library."""
        user_book, target_user = self.get_object(request, user_id, book_id)

        serializer_context = {"request": request, "target_user": target_user}
        serializer = UserBookListSerializer(user_book.book, context=serializer_context)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, user_id, book_id):
        """Update reading status."""
        user_book, target_user = self.get_object(request, user_id, book_id)

        serializer = UserBookUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_book.status = serializer.validated_data["status"]
        user_book.save(update_fields=["status", "updated_at"])

        logger.info(
            "Book status updated"
        )

        return Response(
            {"detail": "Book status updated successfully."},
            status=status.HTTP_200_OK,
        )

    def delete(self, request, user_id, book_id):
        """Remove book from library (soft delete)."""
        user_book, target_user = self.get_object(request, user_id, book_id)
        user_book.soft_delete()

        logger.info(
            "Book removed from library"
        )

        return Response(status=status.HTTP_204_NO_CONTENT)
