import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestLoginThrottle:
    url = "/api/auth/login/"

    def test_sixth_attempt_returns_429(self, api_client):
        """
        預設 5/min：第 6 次呼叫同 IP 必須被擋（無論成功或失敗都算）。
        """
        User.objects.create_user(email="test@example.com", username="testuser", password="Aa1!xy", is_active=True)
        # 先 5 次錯密碼（每次 401）
        for _ in range(5):
            resp = api_client.post(self.url, {"email": "test@example.com", "password": "wrong"})
            assert resp.status_code == 401
        # 第 6 次必須被 throttle
        resp = api_client.post(self.url, {"email": "test@example.com", "password": "Aa1!xy"})
        assert resp.status_code == 429

    def test_within_limit_normal_login(self, api_client):
        """
        限定次數內，合法登入照常 200。
        """
        User.objects.create_user(email="test@example.com", username="testuser", password="Aa1!xy", is_active=True)
        resp = api_client.post(self.url, {"email": "test@example.com", "password": "Aa1!xy"})
        assert resp.status_code == 200
