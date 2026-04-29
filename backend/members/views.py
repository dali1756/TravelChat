from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.models import update_last_login
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework_simplejwt.tokens import RefreshToken

from members.emails import send_password_reset_email, send_verification_email
from members.serializers import (
    EMAIL_TAKEN_MESSAGE,
    USERNAME_TAKEN_MESSAGE,
    ChangePasswordSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterSerializer,
    ResendVerifyEmailSerializer,
    SetUserActiveSerializer,
    UserProfileSerializer,
    VerifyEmailSerializer,
)

User = get_user_model()


def blacklist_all_outstanding_tokens(user):
    """
    將指定使用者所有未失效的 refresh token 加入 blacklist，強制所有裝置登出。
    """
    for token in OutstandingToken.objects.filter(user=user):
        BlacklistedToken.objects.get_or_create(token=token)


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = request.data.get("email", "")
        username = request.data.get("username", "")
        try:
            with transaction.atomic():
                user = serializer.save()
        except IntegrityError:
            errors = {}
            if email and User.objects.filter(email__iexact=email).exists():
                errors["email"] = [EMAIL_TAKEN_MESSAGE]
            if username and User.objects.filter(username__iexact=username).exists():
                errors["username"] = [USERNAME_TAKEN_MESSAGE]
            return Response(errors or {"detail": "註冊失敗。"}, status=status.HTTP_400_BAD_REQUEST)
        # user 建立為 is_active = False，寄出驗證信，驗證後才可登入
        send_verification_email(user)
        return Response(
            {"detail": "註冊成功，請至信箱點擊驗證連結以啟用帳號。"},
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")
        user = authenticate(request, email=email, password=password)
        if user is None:
            return Response(
                {"detail": "帳號或密碼錯誤。"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        update_last_login(None, user)
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
        )


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response(
                {"refresh": ["必須提供 refresh token。"]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            token = RefreshToken(refresh_token)
        except TokenError:
            return Response(
                {"refresh": ["refresh token 無效或已過期。"]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        # 驗證 refresh token 屬於當前使用者，避免惡意 blacklist 他人 token
        if str(token.get("user_id")) != str(request.user.id):
            return Response(
                {"refresh": ["refresh token 與使用者不符。"]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        token.blacklist()
        return Response(status=status.HTTP_205_RESET_CONTENT)


class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class AdminSetUserActiveView(APIView):
    """
    Staff-only API：切換指定使用者的 is_active，停用時強制登出（blacklist 所有 refresh token）。
    """

    permission_classes = [permissions.IsAdminUser]

    def patch(self, request, user_id):
        serializer = SetUserActiveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        target = get_object_or_404(User, pk=user_id)
        target.is_active = serializer.validated_data["is_active"]
        target.save(update_fields=["is_active", "updated_at"])
        if not target.is_active:
            blacklist_all_outstanding_tokens(target)
        return Response({"id": target.id, "is_active": target.is_active}, status=status.HTTP_200_OK)


class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request):
        user = request.user
        old_password = request.data.get("old_password", "")
        if not user.check_password(old_password):
            return Response(
                {"old_password": ["舊密碼錯誤。"]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password", "updated_at"])
        blacklist_all_outstanding_tokens(user)
        return Response(status=status.HTTP_200_OK)


def _decode_uid_to_user(uid: str):
    """
    解 urlsafe-base64 user pk，失敗或 user 不存在皆回 None。
    """
    try:
        pk = force_str(urlsafe_base64_decode(uid))
        return User.objects.get(pk=pk)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return None


INVALID_TOKEN_MESSAGE = "驗證連結無效或已過期。"


class VerifyEmailView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        serializer = VerifyEmailSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        user = _decode_uid_to_user(serializer.validated_data["uid"])
        if user is None or not PasswordResetTokenGenerator().check_token(user, serializer.validated_data["token"]):
            return Response({"detail": INVALID_TOKEN_MESSAGE}, status=status.HTTP_400_BAD_REQUEST)
        if not user.is_active:
            user.is_active = True
            user.save(update_fields=["is_active", "updated_at"])
        refresh = RefreshToken.for_user(user)
        return Response(
            {"access": str(refresh.access_token), "refresh": str(refresh)},
            status=status.HTTP_200_OK,
        )


class ResendVerifyEmailView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ResendVerifyEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]
        # 手動驗證身份（不走 authenticate()，因為 authenticate 會拒絕 is_active = False 的 user）
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            return Response({"detail": "帳號或密碼錯誤。"}, status=status.HTTP_401_UNAUTHORIZED)
        if not user.check_password(password):
            return Response({"detail": "帳號或密碼錯誤。"}, status=status.HTTP_401_UNAUTHORIZED)
        if user.is_active:
            return Response(
                {"detail": "帳號已完成 email 驗證。"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        send_verification_email(user)
        return Response(
            {"detail": "已重新寄出驗證信，請至信箱點擊連結。"},
            status=status.HTTP_200_OK,
        )


class PasswordResetRequestView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        # 用 public() queryset：admin 帳號無法觸發寄信，與 email 不存在行為一致
        user = User.objects.public().filter(email__iexact=email).first()
        if user is not None:
            send_password_reset_email(user)
        # 不論是否寄信都回一致訊息
        return Response(
            {"detail": "若該 email 存在於系統，我們已寄出重設密碼連結。"},
            status=status.HTTP_200_OK,
        )


class UserSearchView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request, *args, **kwargs):
        query = request.query_params.get("q", "").strip()
        if not query:
            return Response([])
        qs = (
            User.objects.public()
            .filter(username__istartswith=query, is_active=True)
            .exclude(pk=request.user.pk)
            .values("id", "username")[:20]
        )
        return Response(list(qs))


class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = _decode_uid_to_user(serializer.validated_data["uid"])
        if user is None or not PasswordResetTokenGenerator().check_token(user, serializer.validated_data["token"]):
            return Response({"detail": INVALID_TOKEN_MESSAGE}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password", "updated_at"])
        blacklist_all_outstanding_tokens(user)
        return Response({"detail": "密碼已重設，請使用新密碼登入。"}, status=status.HTTP_200_OK)
