import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core import mail
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


def _uid_token(user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = PasswordResetTokenGenerator().make_token(user)
    return uid, token


@pytest.mark.django_db
class TestPasswordResetRequest:
    url = "/api/auth/password-reset/request/"

    def test_existing_email_sends_mail(self, api_client):
        User.objects.create_user(email="test@example.com", username="testuser", password="Aa1!xy", is_active=True)
        response = api_client.post(self.url, {"email": "test@example.com"})
        assert response.status_code == 200
        assert len(mail.outbox) == 1
        assert "reset-password" in mail.outbox[0].body

    def test_nonexistent_email_silent_200(self, api_client):
        response = api_client.post(self.url, {"email": "nobody@example.com"})
        assert response.status_code == 200
        assert len(mail.outbox) == 0

    def test_admin_email_silent_200(self, api_client):
        """以 admin 的 email 請求重設必須回 200 但不寄信，避免洩漏 admin 存在。"""
        User.objects.create_superuser(email="admin@example.com", username="adminboss", password="Aa1!xy")
        response = api_client.post(self.url, {"email": "admin@example.com"})
        assert response.status_code == 200
        assert len(mail.outbox) == 0

    def test_missing_email_field_400(self, api_client):
        response = api_client.post(self.url, {})
        assert response.status_code == 400

    def test_invalid_email_format_400(self, api_client):
        response = api_client.post(self.url, {"email": "not-an-email"})
        assert response.status_code == 400


@pytest.mark.django_db
class TestPasswordResetConfirm:
    url = "/api/auth/password-reset/confirm/"

    def test_success(self, api_client):
        user = User.objects.create_user(
            email="test@example.com", username="testuser", password="Aa1!xy", is_active=True
        )
        uid, token = _uid_token(user)
        response = api_client.post(
            self.url,
            {
                "uid": uid,
                "token": token,
                "new_password": "Bb2@zw",
                "new_password_confirm": "Bb2@zw",
            },
        )
        assert response.status_code == 200

        user.refresh_from_db()
        assert user.check_password("Bb2@zw")
        assert not user.check_password("Aa1!xy")

    def test_success_blacklists_all_tokens(self, api_client):
        user = User.objects.create_user(
            email="test@example.com", username="testuser", password="Aa1!xy", is_active=True
        )
        pre_refresh = str(RefreshToken.for_user(user))
        uid, token = _uid_token(user)
        api_client.post(
            self.url,
            {
                "uid": uid,
                "token": token,
                "new_password": "Bb2@zw",
                "new_password_confirm": "Bb2@zw",
            },
        )
        refresh_resp = api_client.post("/api/auth/token/refresh/", {"refresh": pre_refresh})
        assert refresh_resp.status_code == 401

    def test_invalid_token(self, api_client):
        user = User.objects.create_user(
            email="test@example.com", username="testuser", password="Aa1!xy", is_active=True
        )
        uid, _ = _uid_token(user)
        response = api_client.post(
            self.url,
            {
                "uid": uid,
                "token": "bad",
                "new_password": "Bb2@zw",
                "new_password_confirm": "Bb2@zw",
            },
        )
        assert response.status_code == 400
        user.refresh_from_db()
        assert user.check_password("Aa1!xy")

    def test_invalid_uid(self, api_client):
        response = api_client.post(
            self.url,
            {
                "uid": "!!!not-base64!!!",
                "token": "whatever",
                "new_password": "Bb2@zw",
                "new_password_confirm": "Bb2@zw",
            },
        )
        assert response.status_code == 400

    def test_passwords_mismatch(self, api_client):
        user = User.objects.create_user(
            email="test@example.com", username="testuser", password="Aa1!xy", is_active=True
        )
        uid, token = _uid_token(user)
        response = api_client.post(
            self.url,
            {
                "uid": uid,
                "token": token,
                "new_password": "Bb2@zw",
                "new_password_confirm": "Bb2@ZZ",
            },
        )
        assert response.status_code == 400
        assert "new_password_confirm" in response.data

    def test_weak_password(self, api_client):
        user = User.objects.create_user(
            email="test@example.com", username="testuser", password="Aa1!xy", is_active=True
        )
        uid, token = _uid_token(user)
        response = api_client.post(
            self.url,
            {
                "uid": uid,
                "token": token,
                "new_password": "weak",
                "new_password_confirm": "weak",
            },
        )
        assert response.status_code == 400
        assert "new_password" in response.data
