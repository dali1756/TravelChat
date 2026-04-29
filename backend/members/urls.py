from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from members.views import (
    AdminSetUserActiveView,
    ChangePasswordView,
    LoginView,
    LogoutView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    RegisterView,
    ResendVerifyEmailView,
    UserProfileView,
    UserSearchView,
    VerifyEmailView,
)

auth_urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("verify-email/", VerifyEmailView.as_view(), name="verify_email"),
    path("verify-email/resend/", ResendVerifyEmailView.as_view(), name="verify_email_resend"),
    path("password-reset/request/", PasswordResetRequestView.as_view(), name="password_reset_request"),
    path("password-reset/confirm/", PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
]

members_urlpatterns = [
    path("me/", UserProfileView.as_view(), name="user_profile"),
    path("me/password/", ChangePasswordView.as_view(), name="change_password"),
    path("search/", UserSearchView.as_view(), name="user_search"),
]

admin_urlpatterns = [
    path("members/<int:user_id>/active/", AdminSetUserActiveView.as_view(), name="admin_set_user_active"),
]
