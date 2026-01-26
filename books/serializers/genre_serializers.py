from rest_framework import serializers
from books.models import Genre


class GenreSerializer(serializers.ModelSerializer):

    def validate_name(self, value):
        value = value.strip().lower()
        request = self.context["request"]
        tenant = request.user.tenant
        if Genre.objects.filter(tenant=tenant, name=value).exists():
            raise serializers.ValidationError("A genre with this name already exists.")
        return value

    class Meta:
        model = Genre
        fields = ["id", "name", "description", "created_at"]
        read_only_fields = ["id", "created_at"]
