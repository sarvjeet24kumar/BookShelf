from django.urls import path
from .views import BookListCreateView

urlpatterns = [
    path("books/", BookListCreateView.as_view(), name="list"),
    # path("books/<uuid:id>/", AddBookView.as_view(), name="list"),
]
