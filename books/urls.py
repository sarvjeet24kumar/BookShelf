from django.urls import path
from .views import (
    BookView,
    MyBookView,
    MyBookDetailView,
    BookDetailView,
    GenreListView,
)

urlpatterns = [
    path("books/", BookView.as_view(), name="list"),
    path("books/<uuid:id>/", BookDetailView.as_view(), name="book-detail"),
    path("my-books/", MyBookView.as_view(), name="my-books"),
    path("my-books/<uuid:id>/", MyBookDetailView.as_view(), name="my-books-detail"),
    path("genres/", GenreListView.as_view(), name="genres"),
]
