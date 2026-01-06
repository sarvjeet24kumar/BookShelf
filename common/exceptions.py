from rest_framework.views import exception_handler
from rest_framework.exceptions import PermissionDenied, NotAuthenticated


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        # Permission errors
        if isinstance(exc, (PermissionDenied, NotAuthenticated)):
            response.data = {"error": response.data.get("detail")}

    return response
