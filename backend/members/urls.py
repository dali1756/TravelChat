from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from members.views import (
    ChangePasswordView,
    LoginView,
    LogoutView,
    RegisterView,
    UserProfileView,
)

auth_urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]

members_urlpatterns = [
    path("me/", UserProfileView.as_view(), name="user_profile"),
    path("me/password/", ChangePasswordView.as_view(), name="change_password"),
]
