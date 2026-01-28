import logging
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from common.throttling import IPThrottle, AuthThrottle
from accounts.serializers.auth_serializers import ChangePasswordSerializer

logger = logging.getLogger(__name__)
User = get_user_model()


class ChangePasswordView(APIView):
    """
    Allow authenticated users to change their password.
    Requires current password verification for security.
    """
    
    permission_classes = [IsAuthenticated]
    throttle_classes = [IPThrottle, AuthThrottle]
    
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        current_password = serializer.validated_data['current_password']
        new_password = serializer.validated_data['new_password']
        
        user = request.user
        
        if not user.check_password(current_password):
            raise ValidationError({"current_password": "Current password is incorrect."})
        
        user.set_password(new_password)
        user.save(update_fields=['password', 'updated_at'])
        
        logger.info(f"Password changed successfully: user_id={user.id}, username={user.username}")
        
        return Response(
            {"detail": "Password changed successfully. Please login with your new password."},
            status=status.HTTP_200_OK
        )
