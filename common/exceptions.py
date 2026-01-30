import logging
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.db import IntegrityError
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
from django.http import JsonResponse
from django.shortcuts import render


logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom exception handler that provides consistent error responses.
    """
    view = context.get("view")
    request = context.get("request")
    view_name = view.__class__.__name__ if view else "Unknown"

    response = exception_handler(exc, context)

    if isinstance(exc, ObjectDoesNotExist):
        exc = NotFound()
        

    if response is None or response.status_code >= 500:
        logger.exception(
            "Unhandled exception in %s | path=%s",
            view_name,
            getattr(request, "path", None),
        )

    if response is None:
        return Response(
            {
                "success": False,
                "error": {
                    "code": "SERVER_ERROR",
                    "message": "Internal server error",
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


    error = {
        "code": response.status_code,
        "message": None,
        "details": None,
    }

    if isinstance(exc, ValidationError):
        error["code"] = "VALIDATION_ERROR"
        error["message"] = "Invalid input"
        error["details"] = response.data

    elif isinstance(exc, (NotAuthenticated, AuthenticationFailed)):
        error["code"] = "AUTHENTICATION_FAILED"
        error["message"] = response.data.get("detail", "Authentication failed")

    elif isinstance(exc, PermissionDenied):
        error["code"] = "PERMISSION_DENIED"
        error["message"] = response.data.get("detail", "Permission denied")

    elif isinstance(exc, (NotFound, Http404)):
        error["code"] = "NOT_FOUND"
        error["message"] = response.data.get("detail", "Resource not found")

    elif isinstance(exc, Throttled):
        error["code"] = "THROTTLED"
        error["message"] = response.data.get("detail", "Too many requests")
        error["details"] = {"retry_after": exc.wait}

    elif isinstance(exc, ParseError):
        error["code"] = "PARSE_ERROR"
        error["message"] = response.data.get("detail", "Malformed request")

    elif isinstance(exc, MethodNotAllowed):
        error["code"] = "METHOD_NOT_ALLOWED"
        error["message"] = response.data.get("detail")

    elif isinstance(exc, APIException):
        error["code"] = "API_ERROR"
        error["message"] = response.data.get("detail", str(exc))

    else:
        error["code"] = "SERVER_ERROR"
        error["message"] = "Internal server error"

    response.data = {
        "success": False,
        "error": error,
    }

    return response

def handler404(request, exception, template_name="404.html"):
    """Custom 404 handler - returns JSON for API routes."""
    
    if request.path.startswith("/api/"):
        return JsonResponse(
            {
                "success": False,
                "error": {
                    "code": "ENDPOINT_NOT_FOUND",
                    "message": "API endpoint does not exist",
                }
            },
            status=404
        )
    return render(request, template_name, status=404)


def handler500(request, template_name="500.html"):
    """Custom 500 handler - returns JSON for API routes."""
    
    logger.exception("Internal server error at %s", request.path)
    
    if request.path.startswith("/api/"):
        return JsonResponse(
            {
                "success": False,
                "error": {
                    "code": "SERVER_ERROR",
                    "message": "Internal server error",
                }
            },
            status=500
        )
    return render(request, template_name, status=500)
