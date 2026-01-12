import logging
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from rest_framework.views import exception_handler
from rest_framework.exceptions import (
    APIException,
    AuthenticationFailed,
    MethodNotAllowed,
    NotAuthenticated,
    NotFound,
    ParseError,
    PermissionDenied,
    Throttled,
    ValidationError,
)

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom exception handler for DRF that:
    - Logs all unexpected exceptions
    - Formats all error responses consistently
    - Handles all common DRF and Django exceptions
    """
    view = context.get("view", None)
    view_name = view.__class__.__name__ if view else "Unknown"

    response = exception_handler(exc, context)

    if not isinstance(
        exc,
        (
            ValidationError,
            PermissionDenied,
            NotAuthenticated,
            AuthenticationFailed,
            NotFound,
            Http404,
            Throttled,
        ),
    ):
        logger.exception(
            "Exception in %s: %s",
            view_name,
            str(exc),
        )

    if response is not None:
        error_data = {}

        if isinstance(exc, ValidationError):
            # Validation errors (400)
            error_data = {"errors": response.data}

        elif isinstance(exc, (PermissionDenied, NotAuthenticated, AuthenticationFailed)):
            # Permission/Auth errors (403/401)
            detail = response.data.get("detail", str(exc))
            error_data = {"error": detail}

        elif isinstance(exc, (NotFound, Http404)):
            # Not found errors (404)
            detail = response.data.get("detail", "Not found")
            error_data = {"error": detail}

        elif isinstance(exc, Throttled):
            # Rate limiting errors (429)
            detail = response.data.get("detail", "Request was throttled")
            error_data = {
                "error": detail,
                "available_in": exc.wait if hasattr(exc, "wait") else None,
            }

        elif isinstance(exc, ParseError):
            # JSON parse errors (400)
            detail = response.data.get("detail", "Malformed request")
            error_data = {"error": detail}

        elif isinstance(exc, MethodNotAllowed):
            # Method not allowed (405)
            detail = response.data.get("detail", f"Method {exc.method} not allowed")
            error_data = {"error": detail}

        elif isinstance(exc, APIException):
            # Generic API exceptions
            detail = response.data.get("detail", str(exc))
            error_data = {"error": detail}

        else:
            # Fallback for any other exception
            error_data = {"error": response.data}

        response.data = error_data


    return response

