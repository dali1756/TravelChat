import pytest
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


@pytest.mark.django_db
class TestLogoutAPI:
    url = "/api/auth/logout/"

    def _create_user_and_tokens(self):
        user = User.objects.create_user(email="test@example.com", username="testuser", password="Aa1!xy")
        refresh = RefreshToken.for_user(user)
        return user, str(refresh), str(refresh.access_token)

    def test_success(self, api_client):
        _, refresh, access = self._create_user_and_tokens()
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        response = api_client.post(self.url, {"refresh": refresh})
        assert response.status_code == 205

    def test_blacklisted_refresh_cannot_refresh(self, api_client):
        _, refresh, access = self._create_user_and_tokens()
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        logout_response = api_client.post(self.url, {"refresh": refresh})
        assert logout_response.status_code == 205

        api_client.credentials()
        refresh_response = api_client.post("/api/auth/token/refresh/", {"refresh": refresh})
        assert refresh_response.status_code == 401

    def test_missing_refresh_field(self, api_client):
        _, _, access = self._create_user_and_tokens()
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        response = api_client.post(self.url, {})
        assert response.status_code == 400
        assert "refresh" in response.data

    def test_invalid_refresh_token(self, api_client):
        _, _, access = self._create_user_and_tokens()
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        response = api_client.post(self.url, {"refresh": "not-a-real-token"})
        assert response.status_code == 400
        assert "refresh" in response.data

    def test_unauthenticated(self, api_client):
        _, refresh, _ = self._create_user_and_tokens()
        response = api_client.post(self.url, {"refresh": refresh})
        assert response.status_code == 401
