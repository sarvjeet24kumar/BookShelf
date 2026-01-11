from rest_framework import serializers
from django.contrib.auth import authenticate
from accounts.models import User
from common.validators import validate_password
from common.constants import MIN_PASSWORD_LENGTH


class SignupSerializer(serializers.ModelSerializer):

    password_confirm = serializers.CharField(
        write_only=True, min_length=MIN_PASSWORD_LENGTH
    )

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "password",
            "password_confirm",
            "first_name",
            "last_name",
            "phone_no",
        )
        extra_kwargs = {
            "email": {"required": True},
            "username": {"required": True},
            "phone_no": {"required": True},
            "first_name": {"required": True},
            "last_name": {"required": True},
            "password": {"write_only": True},
        }

    def validate_username(self, value):
        return value.strip()

    def validate_password(self, value):
        validate_password(value)
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError("Passwords don't match.")
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        password = validated_data.pop("password")
        user = User.objects.create_user(password=password, **validated_data)
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        username = attrs.get("username")
        password = attrs.get("password")

        if not username or not password:
            raise serializers.ValidationError("username and password are required.")

        user = authenticate(
            request=self.context.get("request"),
            username=username,
            password=password,
        )

        if not user:
            raise serializers.ValidationError({"error": "Invalid credentials."})

        if user.deleted_at:
            raise serializers.ValidationError({"error": "This account is inactive."})

        attrs["user"] = user
        return attrs
