from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny


@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    """
    Health check API endpoint.
    Used for monitoring application status.
    """
    return JsonResponse(
        {
            "status": "success",
            "message": "Application is healthy.",
        },
        status=200,
    )
