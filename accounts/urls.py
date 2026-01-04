from django.urls import path
from accounts.views.auth_views import SignupView, LoginView, LogoutView
from accounts.views.user_views import UserListView, UserDetailView

urlpatterns = [
    path("auth/signup/", SignupView.as_view(), name="signup"),
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    path("users/", UserListView.as_view(), name="users"),
    path("users/<uuid:id>/", UserDetailView.as_view(), name="user-delete"),
]
