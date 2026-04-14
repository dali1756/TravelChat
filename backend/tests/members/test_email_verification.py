import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core import mail
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

User = get_user_model()


def _uid_token(user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = PasswordResetTokenGenerator().make_token(user)
    return uid, token


@pytest.mark.django_db
class TestRegisterSendsVerificationEmail:
    def test_register_sends_email(self, api_client):
        data = {
            "username": "newuser",
            "email": "new@example.com",
            "password": "Aa1!xy",
            "password_confirm": "Aa1!xy",
        }
        response = api_client.post("/api/auth/register/", data)
        assert response.status_code == 201
        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == ["new@example.com"]
        assert "verify-email" in mail.outbox[0].body


@pytest.mark.django_db
class TestVerifyEmailEndpoint:
    url = "/api/auth/verify-email/"

    def test_success_activates_user_and_returns_jwt(self, api_client):
        user = User.objects.create_user(email="test@example.com", username="testuser", password="Aa1!xy")
        assert user.is_active is False
        uid, token = _uid_token(user)
        response = api_client.get(self.url, {"uid": uid, "token": token})
        assert response.status_code == 200
        assert "access" in response.data
        assert "refresh" in response.data
        user.refresh_from_db()
        assert user.is_active is True

    def test_idempotent_for_already_verified(self, api_client):
        user = User.objects.create_user(
            email="test@example.com", username="testuser", password="Aa1!xy", is_active=True
        )
        uid, token = _uid_token(user)
        response = api_client.get(self.url, {"uid": uid, "token": token})
        assert response.status_code == 200
        user.refresh_from_db()
        assert user.is_active is True

    def test_invalid_token(self, api_client):
        user = User.objects.create_user(email="test@example.com", username="testuser", password="Aa1!xy")
        uid, _ = _uid_token(user)
        response = api_client.get(self.url, {"uid": uid, "token": "garbage-token"})
        assert response.status_code == 400
        user.refresh_from_db()
        assert user.is_active is False

    def test_invalid_uid(self, api_client):
        response = api_client.get(self.url, {"uid": "!!!not-base64!!!", "token": "whatever"})
        assert response.status_code == 400


@pytest.mark.django_db
class TestResendVerifyEmail:
    url = "/api/auth/verify-email/resend/"

    def test_unverified_can_resend(self, api_client):
        User.objects.create_user(email="test@example.com", username="testuser", password="Aa1!xy")
        # 註冊時會寄一次信，清空 outbox 以便判斷重寄這一次
        mail.outbox.clear()
        response = api_client.post(self.url, {"email": "test@example.com", "password": "Aa1!xy"})
        assert response.status_code == 200
        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == ["test@example.com"]

    def test_verified_user_gets_400(self, api_client):
        User.objects.create_user(email="test@example.com", username="testuser", password="Aa1!xy", is_active=True)
        response = api_client.post(self.url, {"email": "test@example.com", "password": "Aa1!xy"})
        assert response.status_code == 400

    def test_wrong_password_401(self, api_client):
        User.objects.create_user(email="test@example.com", username="testuser", password="Aa1!xy")
        response = api_client.post(self.url, {"email": "test@example.com", "password": "wrong"})
        assert response.status_code == 401

    def test_unknown_email_401(self, api_client):
        response = api_client.post(self.url, {"email": "nobody@example.com", "password": "Aa1!xy"})
        assert response.status_code == 401


@pytest.mark.django_db
class TestInactiveUserCannotLogin:
    def test_login_rejected_when_not_active(self, api_client):
        User.objects.create_user(email="test@example.com", username="testuser", password="Aa1!xy")
        response = api_client.post("/api/auth/login/", {"email": "test@example.com", "password": "Aa1!xy"})
        assert response.status_code == 401
