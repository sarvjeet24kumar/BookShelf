from django.urls import path
from .views import (
    BookListCreateView,
    MyBookView,
    MyBookDetailView,
    BookDetailView,
    GenreListView,
)

urlpatterns = [
    path("books/", BookListCreateView.as_view(), name="list"),
    path("books/<str:id>/", BookDetailView.as_view(), name="book-detail"),
    path("my-books/", MyBookView.as_view(), name="my-books"),
    path("my-books/<str:id>/", MyBookDetailView.as_view(), name="my-books-deatails"),
    path("genres/", GenreListView.as_view(), name="genres"),
]
