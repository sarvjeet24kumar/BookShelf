import django_filters
from books.models import Book
from common.enums import RequestStatus, BookStatus


class BookFilter(django_filters.FilterSet):
    """Filter for Book model."""

    genre = django_filters.CharFilter(
        field_name="book_genres__genre__name",
        lookup_expr="icontains",
    
    )
    title = django_filters.CharFilter(
        lookup_expr="icontains",

    )
    author = django_filters.CharFilter(
        lookup_expr="icontains",

    )
    request_status = django_filters.CharFilter(
        method="filter_request_status",

    )

    class Meta:
        model = Book
        fields = ["genre", "title", "author", "request_status"]

    def filter_request_status(self, queryset, name, value):
        """Handle comma-separated request_status values. Invalid values are ignored."""
        if value:
            valid_statuses = [choice[0] for choice in RequestStatus.choices]
            statuses = [s.strip().upper() for s in value.split(",")]
            valid_input = [s for s in statuses if s in valid_statuses]
            if valid_input:
                return queryset.filter(request_status__in=valid_input)
        return queryset


class MyBookFilter(django_filters.FilterSet):
    """Filter for user's books (my-books endpoint)."""

    status = django_filters.CharFilter(
        method="filter_status",

    )
    title = django_filters.CharFilter(
        lookup_expr="icontains",

    )
    author = django_filters.CharFilter(
        lookup_expr="icontains",

    )

    class Meta:
        model = Book
        fields = ["status", "title", "author"]

    def filter_status(self, queryset, name, value):
        """Filter by user's reading status. Invalid values are ignored."""
        if value:
            valid_statuses = [choice[0] for choice in BookStatus.choices]
            status = value.upper()
            if status in valid_statuses:
                return queryset.filter(user_books__status=status)
        return queryset
