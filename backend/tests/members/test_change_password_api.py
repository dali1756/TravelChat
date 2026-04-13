import pytest
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


@pytest.mark.django_db
class TestChangePasswordAPI:
    url = "/api/members/me/password/"

    def _create_user_and_auth(self, api_client, password="Aa1!xy"):
        user = User.objects.create_user(email="test@example.com", username="testuser", password=password)
        access = str(RefreshToken.for_user(user).access_token)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        return user

    def test_success(self, api_client):
        user = self._create_user_and_auth(api_client)
        response = api_client.put(
            self.url,
            {
                "old_password": "Aa1!xy",
                "new_password": "Bb2@zw",
                "new_password_confirm": "Bb2@zw",
            },
        )
        assert response.status_code == 200

        user.refresh_from_db()
        assert user.check_password("Bb2@zw")
        assert not user.check_password("Aa1!xy")

    def test_new_password_allows_login(self, api_client):
        self._create_user_and_auth(api_client)
        api_client.put(
            self.url,
            {
                "old_password": "Aa1!xy",
                "new_password": "Bb2@zw",
                "new_password_confirm": "Bb2@zw",
            },
        )
        api_client.credentials()
        response = api_client.post(
            "/api/auth/login/",
            {"email": "test@example.com", "password": "Bb2@zw"},
        )
        assert response.status_code == 200

    def test_wrong_old_password(self, api_client):
        user = self._create_user_and_auth(api_client)
        response = api_client.put(
            self.url,
            {
                "old_password": "wrong",
                "new_password": "Bb2@zw",
                "new_password_confirm": "Bb2@zw",
            },
        )
        assert response.status_code == 400
        assert "old_password" in response.data

        user.refresh_from_db()
        assert user.check_password("Aa1!xy")

    def test_new_password_mismatch(self, api_client):
        user = self._create_user_and_auth(api_client)
        response = api_client.put(
            self.url,
            {
                "old_password": "Aa1!xy",
                "new_password": "Bb2@zw",
                "new_password_confirm": "Bb2@ZZ",
            },
        )
        assert response.status_code == 400
        assert "new_password_confirm" in response.data

        user.refresh_from_db()
        assert user.check_password("Aa1!xy")

    def test_new_password_fails_validator(self, api_client):
        user = self._create_user_and_auth(api_client)
        response = api_client.put(
            self.url,
            {
                "old_password": "Aa1!xy",
                "new_password": "weak",
                "new_password_confirm": "weak",
            },
        )
        assert response.status_code == 400
        assert "new_password" in response.data

        user.refresh_from_db()
        assert user.check_password("Aa1!xy")

    def test_unauthenticated(self, api_client):
        User.objects.create_user(email="test@example.com", username="testuser", password="Aa1!xy")
        response = api_client.put(
            self.url,
            {
                "old_password": "Aa1!xy",
                "new_password": "Bb2@zw",
                "new_password_confirm": "Bb2@zw",
            },
        )
        assert response.status_code == 401
