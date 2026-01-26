from django.urls import path
from .views import (
    BookView,
    BookDetailView,
    GenreListView,
    UserBooksView,
    UserBookDetailView,
)

urlpatterns = [
    path("books/", BookView.as_view(), name="list"),
    path("books/<uuid:id>/", BookDetailView.as_view(), name="book-detail"),
    path("users/<uuid:user_id>/books/", UserBooksView.as_view(), name="user-books"),
    path(
        "users/<uuid:user_id>/books/<uuid:book_id>/",
        UserBookDetailView.as_view(),
        name="user-book-detail",
    ),
    path("genres/", GenreListView.as_view(), name="genres"),
]
