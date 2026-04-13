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
        user = User.objects.create_user(email="test@example.com", username="testuser", password="Aa1!xy")
        self._auth(api_client, user)
        response = api_client.get(self.url)
        assert response.status_code == 200
        assert response.data["email"] == "test@example.com"
        assert response.data["username"] == "testuser"
        assert "id" in response.data
        assert "date_joined" in response.data

    def test_update_profile(self, api_client):
        user = User.objects.create_user(email="test@example.com", username="testuser", password="Aa1!xy")
        self._auth(api_client, user)
        response = api_client.put(self.url, {"username": "newname", "email": "new@example.com"})
        assert response.status_code == 200
        assert response.data["username"] == "newname"
        assert response.data["email"] == "new@example.com"

    def test_unauthenticated_get(self, api_client):
        response = api_client.get(self.url)
        assert response.status_code == 401

    def test_unauthenticated_put(self, api_client):
        response = api_client.put(self.url, {"username": "hack"})
        assert response.status_code == 401

    def test_duplicate_email(self, api_client):
        User.objects.create_user(email="other@example.com", username="other", password="Aa1!xy")
        user = User.objects.create_user(email="test@example.com", username="testuser", password="Aa1!xy")
        self._auth(api_client, user)
        response = api_client.put(self.url, {"username": "testuser", "email": "other@example.com"})
        assert response.status_code == 400
