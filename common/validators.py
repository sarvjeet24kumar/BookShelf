import re
from django.core.validators import RegexValidator, MinLengthValidator
from rest_framework.serializers import ValidationError
from django.utils import timezone

MIN_PUBLISHED_YEAR = 1000


username_validator = RegexValidator(
    regex=r"^[a-zA-Z][a-zA-Z0-9_.-]*$",
    message="Username must start with a small letter and can only contain small letters, numbers, underscores, dots, or hyphens.",
    code="invalid_username",
)


first_name_validator = RegexValidator(
    regex=r"^[A-Za-z][A-Za-z0-9 .'-]*$",
    message="First name must start with a letter and may contain letters, numbers, spaces, dots, hyphens, or apostrophes.",
    code="invalid_first_name",
)

last_name_validator = RegexValidator(
    regex=r"^[A-Za-z][A-Za-z0-9 .'-]*$",
    message="Last name must start with a letter and may contain letters, numbers, spaces, dots, hyphens, or apostrophes.",
    code="invalid_last_name",
)

phone_number_validator = RegexValidator(
    r"^\+91\d{10}$",
    "Enter a valid phone number in the format: +91XXXXXXXXXX.",
)


def validate_password(value):
    """
    Validates the password with the following conditions:
    - Must be at least 8 characters long.
    - Must contain at least one letter.
    - Must contain at least one digit.
    - Must contain at least one special character.
    """
    min_length = 8
    special_char_pattern = r'[!@#$%^&*(),.?":{}|<>]'
    digit_pattern = r"\d"
    letter_pattern = r"[a-zA-Z]"

    if len(value) < min_length:
        raise ValidationError("Password must be at least 8 characters long.")

    if not re.search(letter_pattern, value):
        raise ValidationError("Password must contain at least one letter.")

    if not re.search(digit_pattern, value):
        raise ValidationError("Password must contain at least one digit.")

    if not re.search(special_char_pattern, value):
        raise ValidationError("Password must contain at least one special character.")

    return value


title_validator = RegexValidator(
    regex=r"^[a-zA-Z0-9\s_'.,:;!?()@#&-]+$",
    message="Title can only contain letters, numbers, spaces, and common punctuation (@, #, &, etc.).",
    code="invalid_title",
)

author_validator = RegexValidator(
    regex=r"^[A-Za-z][A-Za-z0-9 .'-]*$",
    message="Author must start with a letter and may contain letters, numbers, spaces, dots, hyphens, or apostrophes.",
    code="invalid_author",
)


def isbn_validator(value):
    """
    Validates ISBN-10 or ISBN-13 format.
    - ISBN-10: 10 characters (digits, last can be 'X')
    - ISBN-13: 13 digits
    """

    if not (re.match(r"^[0-9]{9}[0-9X]$", value) or re.match(r"^[0-9]{13}$", value)):
        raise ValidationError(
            "ISBN must be either 10 characters (digits, last can be 'X') or 13 digits."
        )


def published_year_validator(value):
    """Validates published year is between 1000 and current year."""

    current_year = timezone.now().year

    if value < MIN_PUBLISHED_YEAR:
        raise ValidationError(f"Published year must be at least {MIN_PUBLISHED_YEAR}.")

    if value > current_year:
        raise ValidationError(
            f"Published year cannot be in the future. Maximum allowed is {current_year}."
        )
