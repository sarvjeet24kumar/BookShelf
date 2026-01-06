from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from common.pegination import CommonPegination
from .models import Book
from .serializers import BookListSerializer, BookCreateSerializer


class BookListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        genre_filter = request.query_params.get("genre")
        title_filter = request.query_params.get("title")

        queryset = Book.objects.filter(deleted_at__isnull=True)
        if genre_filter:
            queryset = queryset.filter(
                book_genres__genre__name__iexact=genre_filter,
                book_genres__deleted_at__isnull=True,
            )

        if title_filter:
            queryset = queryset.filter(title__contains=title_filter)

        queryset = queryset.distinct().prefetch_related("book_genres__genre")
        paginator = CommonPegination()

        paginated_queryset = paginator.paginate_queryset(queryset, request)
        serializer = BookListSerializer(
            queryset, many=True, context={"request": request}
        )
        return paginator.get_paginated_response(serializer.data)


    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        if user.role != "ADMIN":
            return Response(
                {"detail": "Only admins can create books."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = BookCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        book = serializer.save()

        return Response(
            {
                "message": "Book created successfully",
                "book": BookListSerializer(book, context={"request": request}).data,
            },
            status=status.HTTP_201_CREATED,
        )
