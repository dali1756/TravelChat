from django.contrib.auth import authenticate, get_user_model
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from members.serializers import (
    EMAIL_TAKEN_MESSAGE,
    USERNAME_TAKEN_MESSAGE,
    ChangePasswordSerializer,
    RegisterSerializer,
    UserProfileSerializer,
)

User = get_user_model()


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
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")
        user = authenticate(request, email=email, password=password)
        if user is None:
            return Response(
                {"detail": "帳號或密碼錯誤。"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        user.last_login_time = timezone.now()
        user.save(update_fields=["last_login_time"])
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
            RefreshToken(refresh_token).blacklist()
        except TokenError:
            return Response(
                {"refresh": ["refresh token 無效或已過期。"]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_205_RESET_CONTENT)


class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


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
        return Response(status=status.HTTP_200_OK)
