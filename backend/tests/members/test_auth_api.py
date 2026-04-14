import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestRegisterAPI:
    url = "/api/auth/register/"

    def test_success(self, api_client):
        data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "Aa1!xy",
            "password_confirm": "Aa1!xy",
        }
        response = api_client.post(self.url, data)
        assert response.status_code == 201
        # 註冊完不直接給 JWT；需先完成 email 驗證才能登入
        assert "access" not in response.data
        assert "refresh" not in response.data
        user = User.objects.get(email="test@example.com")
        assert user.is_active is False

    def test_duplicate_email(self, api_client):
        User.objects.create_user(email="test@example.com", username="existing", password="Aa1!xy", is_active=True)
        data = {
            "username": "newuser",
            "email": "test@example.com",
            "password": "Aa1!xy",
            "password_confirm": "Aa1!xy",
        }
        response = api_client.post(self.url, data)
        assert response.status_code == 400

    def test_duplicate_username(self, api_client):
        User.objects.create_user(email="other@example.com", username="testuser", password="Aa1!xy", is_active=True)
        data = {
            "username": "testuser",
            "email": "new@example.com",
            "password": "Aa1!xy",
            "password_confirm": "Aa1!xy",
        }
        response = api_client.post(self.url, data)
        assert response.status_code == 400

    def test_password_mismatch(self, api_client):
        data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "Aa1!xy",
            "password_confirm": "Aa1!xz",
        }
        response = api_client.post(self.url, data)
        assert response.status_code == 400

    def test_weak_password(self, api_client):
        data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "weak",
            "password_confirm": "weak",
        }
        response = api_client.post(self.url, data)
        assert response.status_code == 400


@pytest.mark.django_db
class TestLoginAPI:
    url = "/api/auth/login/"

    def test_success(self, api_client):
        User.objects.create_user(email="test@example.com", username="testuser", password="Aa1!xy", is_active=True)
        response = api_client.post(self.url, {"email": "test@example.com", "password": "Aa1!xy"})
        assert response.status_code == 200
        assert "access" in response.data
        assert "refresh" in response.data

    def test_invalid_credentials(self, api_client):
        User.objects.create_user(email="test@example.com", username="testuser", password="Aa1!xy", is_active=True)
        response = api_client.post(self.url, {"email": "test@example.com", "password": "wrong"})
        assert response.status_code == 401


@pytest.mark.django_db
class TestTokenRefreshAPI:
    def test_success(self, api_client):
        User.objects.create_user(email="test@example.com", username="testuser", password="Aa1!xy", is_active=True)
        login_response = api_client.post("/api/auth/login/", {"email": "test@example.com", "password": "Aa1!xy"})
        refresh_token = login_response.data["refresh"]
        response = api_client.post("/api/auth/token/refresh/", {"refresh": refresh_token})
        assert response.status_code == 200
        assert "access" in response.data

    def test_invalid_token(self, api_client):
        response = api_client.post("/api/auth/token/refresh/", {"refresh": "invalid-token"})
        assert response.status_code == 401
