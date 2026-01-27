from rest_framework import serializers
from common.serializers.base import BaseModelSerializer
from books.models import Genre


class GenreSerializer(BaseModelSerializer):

    def validate_name(self, value):
        value = value.strip().lower()
        request = self.context["request"]
        tenant = request.user.tenant

        # Exclude current instance when updating
        queryset = Genre.objects.filter(tenant=tenant, name=value)
        if self.instance:
            queryset = queryset.exclude(id=self.instance.id)

        if queryset.exists():
            raise serializers.ValidationError("A genre with this name already exists.")
        return value

    class Meta:
        model = Genre
        fields = ["id", "name", "description", "created_at", "deleted_at"]
        read_only_fields = ["id", "created_at"]
