from django.urls import path
from accounts.views.auth_views import SignupView

urlpatterns = [
    path("auth/signup/", SignupView.as_view(), name="signup"),
]
