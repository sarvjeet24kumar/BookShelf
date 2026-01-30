import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied
from books.models import Book
from books.models import UserBook
from books.serializers import (
    BookListSerializer,
    BookCreateSerializer,
    BookUpdateSerializer,
)
from books.filters import BookFilter
from books.services.book_cache_service import book_cache_service
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
        tenant_id = str(user.tenant_id) if user.tenant_id else None
        is_admin = user.role == UserRole.ADMIN

        use_cache = not request.query_params and tenant_id

        if use_cache:
            cache_status = UserRole.ADMIN.lower() if is_admin else UserRole.USER.lower()
            cached_books = book_cache_service.get_books_for_tenant(
                tenant_id, status=cache_status
            )

            if cached_books:
                logger.debug(f"Cache HIT for {cache_status}")
                paginator = CommonPagination()
                page = paginator.paginate_queryset(cached_books, request)
                return paginator.get_paginated_response(
                    page if page is not None else cached_books
                )

        if is_admin:
            queryset = Book.all_objects.filter(
                tenant_id=user.tenant_id
            )
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

        if use_cache and not cached_books:
            books_list = list(queryset)
            cache_status = UserRole.ADMIN.lower() if is_admin else UserRole.USER.lower()
            book_cache_service.set_books_cache(
                tenant_id, books_list, status=cache_status
            )
            logger.debug(f"Cache POPULATED for {cache_status}")
            queryset = books_list

        paginator = CommonPagination()
        paginated_queryset = paginator.paginate_queryset(queryset, request)
        exclude_fields = []
        if request.user.role != UserRole.ADMIN:
            exclude_fields.append("deleted_at")

        serializer = BookListSerializer(
            paginated_queryset,
            many=True,
            exclude_fields=exclude_fields,
            context={"request": request},
        )
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = BookCreateSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        book = serializer.save()

        logger.info("Book created successfully")

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
        exclude_fields = []
        if request.user.role != UserRole.ADMIN:
            exclude_fields.append("deleted_at")

        serializer = BookListSerializer(
            book, exclude_fields=exclude_fields, context={"request": request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, id):
        book = self.get_object(id, request.user)
        user = request.user

        is_admin = user.role == UserRole.ADMIN
        is_owner = book.created_by == user
        is_pending = book.request_status == RequestStatus.PENDING

        if not (is_admin or (is_owner and is_pending)):
            logger.warning(
                "Blocked: Unauthorized update attempt"
            )
            if not is_admin and is_owner and not is_pending:
                raise PermissionDenied(
                    "Cannot update book once it is approved/rejected."
                )
            raise PermissionDenied("You do not have permission to update this book.")

        serializer = BookUpdateSerializer(
            book, data=request.data, partial=True, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        updated_book = serializer.save()

        logger.info("Book updated successfully")

        response_serializer = BookListSerializer(
            updated_book, context={"request": request}
        )
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, id):
        if request.user.role != UserRole.ADMIN:
            logger.warning(
                "Blocked: Non-admin tried to delete book"
            )
            raise PermissionDenied("Only admins can delete books.")

        book = self.get_object(id, request.user)
        active_user_books = UserBook.objects.filter(book=book).exists()

        if active_user_books:
            logger.warning(
                "Blocked: Cannot delete book in user libraries"
            )
            return Response(
                {
                    "error": "Cannot delete this book. It exists in one or more user libraries. "
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        book.soft_delete()

        book.book_genres.update(deleted_at=book.deleted_at)

        logger.info(
            "Book soft-deleted by admin"
        )

        return Response(status=status.HTTP_204_NO_CONTENT)
