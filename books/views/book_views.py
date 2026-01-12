import logging
from django.utils import timezone
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
from common.enums import UserRole, RequestStatus, Visibility
from django.db.models import Q

logger = logging.getLogger(__name__)


class BookView(APIView):

    def get(self, request):
        user = request.user
        queryset = Book.objects.filter(deleted_at__isnull=True)

        if user.role != UserRole.ADMIN:
            queryset = queryset.filter(
                Q(request_status=RequestStatus.APPROVED, visibility=Visibility.PUBLIC)
                | Q(created_by=user)
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

    def get_book_or_404(self, id):
        """Get book by ID or raise NotFound exception."""
        book = Book.objects.filter(id=id, deleted_at__isnull=True).first()

        if not book:
            raise NotFound("Book not found.")

        return book

    def get(self, request, id):
        book = self.get_book_or_404(id)

        if request.user.role != UserRole.ADMIN:
            is_approved_public = (
                book.request_status == RequestStatus.APPROVED
                and book.visibility == Visibility.PUBLIC
            )
            is_own_book = book.created_by == request.user

            if not (is_approved_public or is_own_book):
                raise NotFound("Book not found.")

        serializer = BookListSerializer(book, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, id):

        if request.user.role != UserRole.ADMIN:
            logger.warning(
                "Blocked: Non-admin tried to update book: book_id=%s, user_id=%s",
                id,
                request.user.id,
            )
            raise PermissionDenied("Only admins can update books.")

        book = self.get_book_or_404(id)

        serializer = BookUpdateSerializer(book, data=request.data, partial=True)
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

        book = self.get_book_or_404(id)

        book.deleted_at = timezone.now()
        book.save(update_fields=["deleted_at"])

        book.book_genres.update(deleted_at=timezone.now())

        logger.info(
            "Book soft-deleted: book_id=%s, deleted_by=%s", book.id, request.user.id
        )

        return Response(
            status=status.HTTP_204_NO_CONTENT,
        )
