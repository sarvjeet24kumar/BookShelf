from rest_framework import serializers
from common.serializers.base import BaseModelSerializer
from django.contrib.auth import get_user_model
from common.validators import validate_password
from common.enums import UserRole
from accounts.services import email_verification_service

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "password",
            "phone_no",
            "role",
            "tenant",
            "first_name",
            "last_name",
            "deleted_at",
            "created_at",
        ]
        read_only_fields = ["id", "created_at", "deleted_at"]
        extra_kwargs = {
            "password": {"write_only": True},
            "role": {"required": False},
            "tenant": {"required": False},
        }

    def validate_username(self, value):
        value = value.lower()
        if User.all_objects.filter(username=value).exists():
            raise serializers.ValidationError(
                "A user with this username already exists."
            )
        return value

    def validate_email(self, value):
        return value.lower()

    def create(self, validated_data):
        password = validated_data.pop("password")
        return User.objects.create_user(password=password, **validated_data)


class UserDetailSerializer(BaseModelSerializer):

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "password",
            "phone_no",
            "role",
            "first_name",
            "last_name",
            "is_active",
            "deleted_at",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]
        extra_kwargs = {"password": {"write_only": True}}

    def validate_username(self, value):
        value = value.strip().lower()
        queryset = User.objects.filter(username=value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError("user with this username already exists.")
        return value

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)

        for attr, value in validated_data.items():
            if isinstance(value, str):
                value = value.strip()
            setattr(instance, attr, value)

        if password:

            validate_password(password)
            instance.set_password(password)
        instance.full_clean(exclude=["deleted_at", "created_at", "updated_at", "id"])
        instance.save()
        return instance
