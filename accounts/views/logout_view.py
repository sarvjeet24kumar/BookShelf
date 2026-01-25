import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import ValidationError


logger = logging.getLogger(__name__)


class LogoutView(APIView):
    """
    User logout - blacklist refresh token.
    
    """

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            raise ValidationError("Refresh token is required.")
        
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError:
            raise ValidationError("Invalid or expired token.")
        
        logger.info("User logged out: user_id=%s", request.user.id)
        return Response({"detail": "Logout successful."})
