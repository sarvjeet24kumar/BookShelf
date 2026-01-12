from django.http import JsonResponse
from django.urls import resolve
from django.urls.exceptions import Resolver404


class API404Middleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            resolve(request.path_info)
        except Resolver404:
            if request.path_info.startswith("/api/"):
                return JsonResponse(
                    {
                        "success": False,
                        "error": {
                            "code": "ENDPOINT_NOT_FOUND",
                            "message": "API endpoint does not exist",
                        },
                    },
                    status=404,
                )

        return self.get_response(request)
