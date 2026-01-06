import uuid
from django.utils import timezone
from rest_framework.views import APIView
from common.permissions import IsUser
from rest_framework.response import Response
from rest_framework import status
from .models import Book, UserBook
from .serializers import BookListSerializer, BookCreateSerializer
from common.pagination import CommonPagination


class BookListCreateView(APIView):

    def get(self, request):
        user = request.user
        genre_filter = request.query_params.get("genre")
        title_filter = request.query_params.get("title")

        queryset = Book.objects.filter(deleted_at__isnull=True)
        if user.role != "ADMIN":
            queryset = queryset.filter(is_active=True)
        if genre_filter:
            queryset = queryset.filter(
                book_genres__genre__name__iexact=genre_filter,
                book_genres__deleted_at__isnull=True,
            )

        if title_filter:
            queryset = queryset.filter(title__contains=title_filter)

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


class MyBookView(APIView):
    permission_classes = [IsUser]

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

        paginator = CommonPagination()
        paginated_queryset = paginator.paginate_queryset(queryset, request)

        serializer = BookListSerializer(
            paginated_queryset,
            many=True,
            context={"request": request},
        )

        return paginator.get_paginated_response(serializer.data)

    def post(self, request):

        book_id = request.data.get("id")
        status_value = request.data.get("status", "TO_READ")

        if not book_id:
            return Response(
                {"detail": "book_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            book_uuid = uuid.UUID(str(book_id))
        except (ValueError, TypeError):
            return Response(
                {"error": "Invalid book_id. Must be a valid UUID."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        book = Book.objects.filter(
            id=book_uuid, deleted_at__isnull=True, is_active=True
        ).first()

        if not book:
            return Response(
                {"error": "Book not available or deleted."},
                status=status.HTTP_404_NOT_FOUND,
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

        user_book.delete()

        return Response(
            {"message": "Book removed from your list."},
            status=status.HTTP_204_NO_CONTENT,
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

        # Users can only see active books, admins can see all
        if request.user.role != "ADMIN" and not book.is_active:
            return Response(
                {"error": "Book not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = BookListSerializer(book, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, id):
        if request.user.role != "ADMIN":
            return Response(
                {"error": "Only admins can update books."},
                status=status.HTTP_403_FORBIDDEN,
            )

        book, error = self.get_book(id)
        if error:
            return error

        book.title = request.data.get("title", book.title)
        book.author = request.data.get("author", book.author)
        book.isbn = request.data.get("isbn", book.isbn)
        book.published_year = request.data.get("published_year", book.published_year)
        book.is_active = request.data.get("is_active", book.is_active)
        book.save()

        genres = request.data.get("genres")
        if genres is not None:
            # Remove existing genres
            book.book_genres.update(deleted_at=timezone.now())

            for genre_name in genres:
                genre, _ = Genre.objects.get_or_create(name=genre_name.strip())
                BookGenre.objects.create(book=book, genre=genre)

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

        if "title" in request.data:
            book.title = request.data["title"]
        if "author" in request.data:
            book.author = request.data["author"]
        if "isbn" in request.data:
            book.isbn = request.data["isbn"]
        if "published_year" in request.data:
            book.published_year = request.data["published_year"]
        if "is_active" in request.data:
            book.is_active = request.data["is_active"]
        book.save()

        if "genres" in request.data:

            book.book_genres.update(deleted_at=timezone.now())
            for genre_name in request.data["genres"]:
                genre, _ = Genre.objects.get_or_create(name=genre_name.strip())
                BookGenre.objects.create(book=book, genre=genre)

        serializer = BookListSerializer(book, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

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

        return Response(
            {"message": "Book deleted successfully."},
            status=status.HTTP_200_OK,
        )
