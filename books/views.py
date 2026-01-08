import uuid
from django.utils import timezone
from rest_framework.views import APIView
from common.permissions import IsUser
from rest_framework.response import Response
from rest_framework import status
from .models import Book, UserBook, Genre, BookGenre
from .serializers import (
    BookListSerializer,
    BookCreateSerializer,
    GenreSerializer,
    BookUpdateSerializer,
)
from common.pagination import CommonPagination
from common.enums import BookStatus
from django.db.models import Q


class BookListCreateView(APIView):

    def get(self, request):
        user = request.user
        genre_filter = request.query_params.get("genre")
        title_filter = request.query_params.get("title")
        request_status = request.query_params.get("request_status")
        request_status_filters = None

        if request_status:
            request_status_filters = request_status.upper().split(",")

        # Base queryset - all non-deleted books
        queryset = Book.objects.filter(deleted_at__isnull=True)

        # Apply role-based filtering
        if user.role != "ADMIN":
            # Regular users can see:
            # 1. APPROVED books (publicly visible)
            # 2. OR books created by themselves (any status)
            queryset = queryset.filter(
                Q(request_status="APPROVED") | Q(created_by=user)
            )

        # Both admin and users can filter by request_status
        if request_status_filters:
            queryset = queryset.filter(request_status__in=request_status_filters)
        if genre_filter:
            queryset = queryset.filter(
                book_genres__genre__name__iexact=genre_filter,
                book_genres__deleted_at__isnull=True,
            )

        if title_filter:
            queryset = queryset.filter(title__icontains=title_filter)

        queryset = queryset.distinct().prefetch_related("book_genres__genre")
        paginator = CommonPagination()

        paginated_queryset = paginator.paginate_queryset(queryset, request)
        serializer = BookListSerializer(
            paginated_queryset, many=True, context={"request": request}
        )
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        user = request.user
        serializer = BookCreateSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        book = serializer.save()

        return Response(
            BookListSerializer(book, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class BookDetailView(APIView):

    def get_book(self, id):
        try:
            book_uuid = uuid.UUID(str(id))
        except (ValueError, TypeError):
            return None, Response(
                {"error": "Invalid book_id. Must be a valid UUID."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        book = Book.objects.filter(id=book_uuid, deleted_at__isnull=True).first()

        if not book:
            return None, Response(
                {"error": "Book not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return book, None

    def get(self, request, id):
        book, error = self.get_book(id)
        if error:
            return error

        if (
            request.user.role != "ADMIN"
            and book.request_status != "APPROVED"
            and book.created_by != request.user
        ):
            return Response(
                {"error": "Book not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = BookListSerializer(book, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, id):

        if request.user.role != "ADMIN":
            return Response(
                {"error": "Only admins can update books."},
                status=status.HTTP_403_FORBIDDEN,
            )

        book, error = self.get_book(id)
        if error:
            return error

        # Use BookUpdateSerializer for validation and update
        serializer = BookUpdateSerializer(book, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated_book = serializer.save()

        response_serializer = BookListSerializer(
            updated_book, context={"request": request}
        )
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, id):
        if request.user.role != "ADMIN":
            return Response(
                {"error": "Only admins can delete books."},
                status=status.HTTP_403_FORBIDDEN,
            )

        book, error = self.get_book(id)
        if error:
            return error

        book.deleted_at = timezone.now()
        book.save()

        book.book_genres.update(deleted_at=timezone.now())

        return Response(
            status=status.HTTP_204_NO_CONTENT,
        )


class MyBookView(APIView):
    permission_classes = [IsUser]

    def get(self, request):
        status_filter = request.query_params.get("status")
        title_filter = request.query_params.get("title")
        author_filter = request.query_params.get("author")
        queryset = (
            Book.objects.filter(
                deleted_at__isnull=True,
                user_books__user=request.user,
                user_books__deleted_at__isnull=True,
            )
            .distinct()
            .prefetch_related("book_genres__genre")
        )
        if status_filter:
            # Validate and filter by reading status
            valid_statuses = BookStatus.values
            if status_filter.upper() in valid_statuses:
                queryset = queryset.filter(user_books__status=status_filter.upper())

        if title_filter:
            queryset = queryset.filter(title__icontains=title_filter)

        if author_filter:
            queryset = queryset.filter(author__icontains=author_filter)

        paginator = CommonPagination()
        paginated_queryset = paginator.paginate_queryset(queryset, request)

        serializer = BookListSerializer(
            paginated_queryset,
            many=True,
            context={"request": request},
        )

        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        if request.user.role != "USER":
            return Response(
                {"error": "Only users can add books to their library."},
                status=status.HTTP_403_FORBIDDEN,
            )

        book_id = request.data.get("id")
        status_value = request.data.get("status", "TO_READ")

        if not book_id:
            return Response(
                {"detail": "book_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        valid_statuses = BookStatus.values
        if status_value not in valid_statuses:
            return Response(
                {"error": f"Invalid status. Allowed values are: {valid_statuses}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            book_uuid = uuid.UUID(str(book_id))
        except (ValueError, TypeError):
            return Response(
                {"error": "Invalid book_id. Must be a valid UUID."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        book = Book.objects.filter(id=book_uuid, deleted_at__isnull=True).first()

        if not book:
            return Response(
                {"error": "Book not available or deleted."},
                status=status.HTTP_404_NOT_FOUND,
            )
        if book.request_status != "APPROVED":
            return Response(
                {
                    "error": f"Only APPROVED books can be added to your library. This book is currently {book.request_status}."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user_book, created = UserBook.objects.get_or_create(
            user=request.user,
            book=book,
            defaults={"status": status_value},
        )

        if not created:
            return Response(
                {"error": "Book already in your list."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {"message": "Book added to your list."},
            status=status.HTTP_201_CREATED,
        )


class MyBookDetailView(APIView):
    permission_classes = [IsUser]

    def get_user_book(self, request, id):
        try:
            book_uuid = uuid.UUID(str(id))
        except (ValueError, TypeError):
            return None, Response(
                {"error": "Invalid book_id. Must be a valid UUID."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user_book = UserBook.objects.filter(
            user=request.user,
            book_id=book_uuid,
            deleted_at__isnull=True,
        ).first()

        if not user_book:
            return None, Response(
                {"error": "Book not found in your list."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return user_book, None

    def get(self, request, id):
        user_book, error = self.get_user_book(request, id)
        if error:
            return error

        book = user_book.book
        serializer = BookListSerializer(book, context={"request": request})
        data = serializer.data
        data.pop("request_status", None)
        data["status"] = user_book.status
        return Response(data, status=status.HTTP_200_OK)

    def patch(self, request, id):
        user_book, error = self.get_user_book(request, id)
        if error:
            return error

        status_value = request.data.get("status")
        if not status_value:
            return Response(
                {"error": "status is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        valid_statuses = BookStatus.values
        if status_value not in valid_statuses:
            return Response(
                {"error": f"Invalid status. Allowed values are: {valid_statuses}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user_book.status = status_value
        user_book.save(update_fields=["status", "updated_at"])

        return Response(
            {"message": "Book status updated successfully."},
            status=status.HTTP_200_OK,
        )

    def delete(self, request, id):
        user_book, error = self.get_user_book(request, id)
        if error:
            return error

        user_book.deleted_at = timezone.now()
        user_book.save()

        return Response(
            status=status.HTTP_204_NO_CONTENT,
        )


class GenreListView(APIView):
    """
    API endpoint to get a list of all genres.
    Any authenticated user can access this endpoint.
    """

    def get(self, request):
        # Get all genres ordered by name
        queryset = Genre.objects.all().order_by("name")

        # Apply pagination
        paginator = CommonPagination()
        paginated_queryset = paginator.paginate_queryset(queryset, request)

        # Serialize the data
        serializer = GenreSerializer(paginated_queryset, many=True)

        # Return paginated response
        return paginator.get_paginated_response(serializer.data)
