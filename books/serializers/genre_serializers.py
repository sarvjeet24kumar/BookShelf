from rest_framework import serializers
from books.models import Genre


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ["id", "name", "description", "created_at"]
        read_only_fields = ["id", "created_at"]
