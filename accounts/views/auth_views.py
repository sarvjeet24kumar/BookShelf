from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.exceptions import ValidationError
from accounts.serializers.auth_serializers import SignupSerializer


class SignupView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            serializer = SignupSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            user = serializer.save()

            return Response(
                {
                    "success": True,
                    "message": "User registered successfully",
                    "data": {"user_id": str(user.id)},
                },
                status=status.HTTP_201_CREATED,
            )

        except ValidationError as e:
            return Response(
                {"success": False, "message": "Validation failed", "errors": e.detail},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception:
            return Response(
                {
                    "success": False,
                    "message": "Internal server error",
                    "error": {
                        "code": "SERVER_ERROR",
                        "detail": "Something went wrong. Please try again later.",
                    },
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
