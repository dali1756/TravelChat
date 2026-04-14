import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestProfileAPI:
    url = "/api/members/me/"

    def _auth(self, api_client, user):
        from rest_framework_simplejwt.tokens import RefreshToken

        token = RefreshToken.for_user(user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")

    def test_get_profile(self, api_client):
        user = User.objects.create_user(
            email="test@example.com", username="testuser", password="Aa1!xy", is_active=True
        )
        self._auth(api_client, user)
        response = api_client.get(self.url)
        assert response.status_code == 200
        assert response.data["email"] == "test@example.com"
        assert response.data["username"] == "testuser"
        assert "id" in response.data
        assert "date_joined" in response.data
        assert "last_login" in response.data

    def test_update_username(self, api_client):
        user = User.objects.create_user(
            email="test@example.com", username="testuser", password="Aa1!xy", is_active=True
        )
        self._auth(api_client, user)
        response = api_client.patch(self.url, {"username": "newname"})
        assert response.status_code == 200
        assert response.data["username"] == "newname"

    def test_put_email_is_ignored(self, api_client):
        """
        email 為唯讀欄位，PUT 帶入新值不會變更帳號 email。
        """
        user = User.objects.create_user(
            email="test@example.com", username="testuser", password="Aa1!xy", is_active=True
        )
        self._auth(api_client, user)
        response = api_client.patch(self.url, {"email": "hacked@example.com"})
        assert response.status_code == 200
        user.refresh_from_db()
        assert user.email == "test@example.com"
        assert response.data["email"] == "test@example.com"

    def test_unauthenticated_get(self, api_client):
        response = api_client.get(self.url)
        assert response.status_code == 401

    def test_unauthenticated_put(self, api_client):
        response = api_client.put(self.url, {"username": "hack"})
        assert response.status_code == 401

    def test_username_conflict_with_normal_user(self, api_client):
        User.objects.create_user(email="other@example.com", username="other", password="Aa1!xy", is_active=True)
        user = User.objects.create_user(
            email="test@example.com", username="testuser", password="Aa1!xy", is_active=True
        )
        self._auth(api_client, user)
        response = api_client.patch(self.url, {"username": "other"})
        assert response.status_code == 400
        assert "username" in response.data

    def test_username_conflict_with_admin_same_message(self, api_client):
        """
        改 username 為 admin 的 username 時，錯誤訊息必須與一般衝突一致。
        """
        User.objects.create_superuser(email="admin@example.com", username="adminboss", password="Aa1!xy")
        User.objects.create_user(email="other@example.com", username="normaluser", password="Aa1!xy", is_active=True)
        user = User.objects.create_user(
            email="test@example.com", username="testuser", password="Aa1!xy", is_active=True
        )
        self._auth(api_client, user)
        resp_admin = api_client.patch(self.url, {"username": "adminboss"})
        resp_normal = api_client.patch(self.url, {"username": "normaluser"})
        assert resp_admin.status_code == 400
        assert resp_normal.status_code == 400
        assert resp_admin.data["username"] == resp_normal.data["username"]

    def test_keep_own_username_does_not_conflict(self, api_client):
        """
        PATCH 自己目前 username 時不應報 unique 錯誤。
        """
        user = User.objects.create_user(
            email="test@example.com", username="testuser", password="Aa1!xy", is_active=True
        )
        self._auth(api_client, user)
        response = api_client.patch(self.url, {"username": "testuser"})
        assert response.status_code == 200
