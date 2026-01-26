import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied
from books.models import Book
from books.serializers import (
    BookListSerializer,
    BookCreateSerializer,
    BookUpdateSerializer,
)
from books.filters import BookFilter
from common.pagination import CommonPagination
from common.enums import UserRole, RequestStatus
from common.permissions import IsTenantMember
from django.db.models import Q

logger = logging.getLogger(__name__)


class BookView(APIView):
    """
    List and create books.
    """

    permission_classes = [IsTenantMember]

    def get(self, request):
        user = request.user
        
        if user.role == UserRole.ADMIN:
            queryset = Book.all_objects.filter(tenant_id=user.tenant_id)
        else:
            queryset = Book.objects.filter(
                Q(request_status=RequestStatus.APPROVED) | Q(created_by=user)
            )

        filterset = BookFilter(request.query_params, queryset=queryset)
        queryset = filterset.qs
        queryset = (
            queryset.distinct()
            .select_related("created_by")
            .prefetch_related("book_genres__genre")
        )

        paginator = CommonPagination()
        paginated_queryset = paginator.paginate_queryset(queryset, request)

        serializer = BookListSerializer(
            paginated_queryset, many=True, context={"request": request}
        )
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = BookCreateSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        book = serializer.save()

        logger.info("Book created: book_id=%s, created_by=%s", book.id, request.user.id)

        return Response(
            BookListSerializer(book, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class BookDetailView(APIView):
    """
    Retrieve, update, or delete a book.
    """

    permission_classes = [IsTenantMember]

    def get_object(self, id, user):
        """Get book by ID (Admins see deleted books)."""
        try:
            if user.role == UserRole.ADMIN:
                return Book.all_objects.get(id=id)
            return Book.objects.get(id=id)
        except Book.DoesNotExist:
            raise NotFound("Book not found.")

    def get(self, request, id):
        book = self.get_object(id, request.user)

        if request.user.role != UserRole.ADMIN:
            is_approved = book.request_status == RequestStatus.APPROVED
            is_own_book = book.created_by == request.user

            if not (is_approved or is_own_book):
                raise NotFound("Book not found.")

        serializer = BookListSerializer(book, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, id):
        book = self.get_object(id, request.user)
        user = request.user

        is_admin = user.role == UserRole.ADMIN
        is_owner = book.created_by == user
        is_pending = book.request_status == RequestStatus.PENDING

        if not (is_admin or (is_owner and is_pending)):
            logger.warning(
                "Blocked: Unauthorized update attempt: book_id=%s, user_id=%s, role=%s, status=%s",
                id,
                user.id,
                user.role,
                book.request_status
            )
            if not is_admin and is_owner and not is_pending:
                raise PermissionDenied("Cannot update book once it is approved/rejected.")
            raise PermissionDenied("You do not have permission to update this book.")

        serializer = BookUpdateSerializer(book, data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        updated_book = serializer.save()

        logger.info("Book updated: book_id=%s, updated_by=%s", book.id, request.user.id)

        response_serializer = BookListSerializer(
            updated_book, context={"request": request}
        )
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, id):
        if request.user.role != UserRole.ADMIN:
            logger.warning(
                "Blocked: Non-admin tried to delete book: book_id=%s, user_id=%s",
                id,
                request.user.id,
            )
            raise PermissionDenied("Only admins can delete books.")

        book = self.get_object(id, request.user)


        book.soft_delete()

        book.book_genres.update(deleted_at=book.deleted_at)

        logger.info(
            "Book soft-deleted: book_id=%s, deleted_by=%s", book.id, request.user.id
        )

        return Response(status=status.HTTP_204_NO_CONTENT)
