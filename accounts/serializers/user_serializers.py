from rest_framework import serializers
from django.contrib.auth import get_user_model
from common.validators import validate_password

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
            "first_name",
            "last_name",
            "created_at",
        ]
        read_only_fields = ["id" "created_at"]
        extra_kwargs = {
            "email": {"required": True},
            "username": {"required": True},
            "phone_no": {"required": True},
            "first_name": {"required": True},
            "last_name": {"required": True},
            "password": {"write_only": True},
            "role": {"required": False},
        }

    def create(self, validated_data):
        password = validated_data.pop("password")
        password = validate_password(password)
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserDetailSerializer(serializers.ModelSerializer):

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
            "created_at",
        ]
        read_only_fields = ["id", "role", "created_at"]
        extra_kwargs = {
            "password": {"write_only": True},
        }

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:

            validate_password(password)
            instance.set_password(password)
        instance.full_clean(exclude=["deleted_at", "created_at", "updated_at", "id"])
        instance.save()
        return instance


class SelfUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "username",
            "password",
            "email",
            "phone_no",
            "role",
            "first_name",
            "last_name",
            "created_at",
        )
        read_only_fields = ("id", "username", "email", "role", "created_at")
        extra_kwargs = {
            "password": {"write_only": True, "required": False},
        }

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
