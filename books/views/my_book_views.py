import logging
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import NotFound, ValidationError
from books.models import Book, UserBook
from books.serializers import (
    MyBookListSerializer,
    MyBookAddSerializer,
    MyBookUpdateSerializer,
)
from books.filters import MyBookFilter
from common.pagination import CommonPagination
from common.enums import BookStatus, RequestStatus, Visibility

logger = logging.getLogger(__name__)


class MyBookView(APIView):

    def get(self, request):
        queryset = (
            Book.objects.filter(
                deleted_at__isnull=True,
                user_books__user=request.user,
                user_books__deleted_at__isnull=True,
            )
            .distinct()
            .prefetch_related("book_genres__genre")
        )

        filterset = MyBookFilter(request.query_params, queryset=queryset)
        queryset = filterset.qs

        paginator = CommonPagination()
        paginated_queryset = paginator.paginate_queryset(queryset, request)

        serializer = MyBookListSerializer(
            paginated_queryset,
            many=True,
            context={"request": request},
        )

        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = MyBookAddSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        book_id = serializer.validated_data["book_id"]
        status_value = serializer.validated_data["status"]

        book = Book.objects.filter(id=book_id, deleted_at__isnull=True).first()

        if not book:
            raise NotFound("Book not available or deleted.")

        if book.request_status != RequestStatus.APPROVED:
            raise ValidationError(
                f"Only APPROVED books can be added. This book is {book.request_status}."
            )

        if book.visibility != Visibility.PUBLIC and book.created_by != request.user:
            raise NotFound("This book is not available.")

        user_book = UserBook.objects.filter(user=request.user, book=book).first()

        if user_book:
            if user_book.deleted_at:
                user_book.deleted_at = None
                user_book.status = status_value
                user_book.save(update_fields=["deleted_at", "status", "updated_at"])
                logger.info(
                    "User restored book to library: book_id=%s, user_id=%s",
                    book.id,
                    request.user.id,
                )
                return Response(
                    {"message": "Book restored to your library."},
                    status=status.HTTP_201_CREATED,
                )
            else:
                raise ValidationError("Book already in your library.")

        UserBook.objects.create(user=request.user, book=book, status=status_value)

        logger.info(
            "User added book to library: book_id=%s, user_id=%s",
            book.id,
            request.user.id,
        )

        return Response(
            {"message": "Book added to your library."},
            status=status.HTTP_201_CREATED,
        )


class MyBookDetailView(APIView):

    def get_user_book_or_404(self, request, id):
        """Get user's book by ID or raise NotFound exception."""
        user_book = UserBook.objects.filter(
            user=request.user,
            book_id=id,
            deleted_at__isnull=True,
        ).first()

        if not user_book:
            raise NotFound("Book not found in your library.")

        return user_book

    def get(self, request, id):
        user_book = self.get_user_book_or_404(request, id)

        serializer = MyBookListSerializer(user_book.book, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, id):
        user_book = self.get_user_book_or_404(request, id)

        serializer = MyBookUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_book.status = serializer.validated_data["status"]
        user_book.save(update_fields=["status", "updated_at"])

        logger.info(
            "User updated book status: book_id=%s, user_id=%s, new_status=%s",
            user_book.book_id,
            request.user.id,
            user_book.status,
        )

        return Response(
            {"message": "Book status updated successfully."},
            status=status.HTTP_200_OK,
        )

    def delete(self, request, id):
        user_book = self.get_user_book_or_404(request, id)

        user_book.deleted_at = timezone.now()
        user_book.save(update_fields=["deleted_at"])

        logger.info(
            "User removed book from library: book_id=%s, user_id=%s",
            user_book.book_id,
            request.user.id,
        )

        return Response(
            status=status.HTTP_204_NO_CONTENT,
        )
