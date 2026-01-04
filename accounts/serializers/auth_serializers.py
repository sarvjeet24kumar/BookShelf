import re
from rest_framework import serializers
from accounts.models import Users
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate
from common.constants import MIN_PASSWORD_LENGTH


class SignupSerializer(serializers.ModelSerializer):

    password = serializers.CharField(write_only=True, min_length=MIN_PASSWORD_LENGTH)
    password_confirm = serializers.CharField(
        write_only=True, min_length=MIN_PASSWORD_LENGTH
    )
    first_name = serializers.CharField(required=True, allow_blank=False)
    last_name = serializers.CharField(allow_blank=True, required=False, allow_null=True)

    class Meta:
        model = Users
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
        }

    def validate_username(self, value):
        username = value.strip()

        if len(username) < 3 or len(username) > 20:
            raise serializers.ValidationError("Username must be 3–20 characters long.")

        pattern = r"^(?=.*[A-Za-z])[A-Za-z0-9]+$"
        if not re.match(pattern, username):
            raise serializers.ValidationError(
                "Username must contain at least one letter and only letters and numbers are allowed."
            )

        return username

    def validate_first_name(self, value):
        return self.validate_alpha(value, "first_name")

    def validate_last_name(self, value):
        return self.validate_alpha(value, "last_name")

    def validate_email(self, value):
        try:
            email = value.strip()
            regex = r"^[a-z0-9._%+-]+@[a-z]+\.[a-z]{2,}$"
            if not re.match(regex, email):
                raise serializers.ValidationError("Invalid email format.")
            return email
        except ValidationError:
            raise serializers.ValidationError("Invalid email format.")

    def validate_phone_no(self, value):
        phone = value.strip()
        if not re.match(r"^\+?1?\d{10,15}$", phone):
            raise serializers.ValidationError("Invalid phone number format.")
        return phone

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError("Passwords don't match.")
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        password = validated_data.pop("password")
        try:
            validate_password(password)
        except ValidationError as e:
            raise serializers.ValidationError(",".join(e))
        user = Users.objects.create_user(password=password, **validated_data)
        user.save()
        return user

    def validate_alpha(self, value, field_name):
        cleaned = value.strip()
        if cleaned == "":
            raise serializers.ValidationError(
                f"{field_name} cannot be empty or spaces only."
            )
        if len(cleaned) < 2:
            raise serializers.ValidationError(
                f"{field_name} must be at least 2 characters."
            )
        if not re.match(r"^[A-Za-z]+$", cleaned):
            raise serializers.ValidationError(
                f"Only alphabets are allowed in {field_name}."
            )

        return cleaned.capitalize()


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True, style={"input_type": "password"})

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
            raise serializers.ValidationError(
                {"error": "This account has been deleted."}
            )

        attrs["user"] = user
        return attrs
