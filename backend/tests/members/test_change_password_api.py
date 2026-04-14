import pytest
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


@pytest.mark.django_db
class TestChangePasswordAPI:
    url = "/api/members/me/password/"

    def _create_user_and_auth(self, api_client, password="Aa1!xy"):
        user = User.objects.create_user(
            email="test@example.com", username="testuser", password=password, is_active=True
        )
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
        User.objects.create_user(email="test@example.com", username="testuser", password="Aa1!xy", is_active=True)
        response = api_client.put(
            self.url,
            {
                "old_password": "Aa1!xy",
                "new_password": "Bb2@zw",
                "new_password_confirm": "Bb2@zw",
            },
        )
        assert response.status_code == 401

    def test_success_blacklists_all_outstanding_tokens(self, api_client):
        """
        修改密碼成功後，所有其他 session（含其他裝置的 refresh token）都必須失效。
        """
        user = User.objects.create_user(
            email="test@example.com", username="testuser", password="Aa1!xy", is_active=True
        )
        # 在其他裝置發 refresh token
        other_device_refresh = str(RefreshToken.for_user(user))
        # 再在這個裝置登入並用這個 access token 改密碼
        current_access = str(RefreshToken.for_user(user).access_token)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {current_access}")
        response = api_client.put(
            self.url,
            {
                "old_password": "Aa1!xy",
                "new_password": "Bb2@zw",
                "new_password_confirm": "Bb2@zw",
            },
        )
        assert response.status_code == 200
        # 其他裝置的 refresh token 應無法再換 access token
        api_client.credentials()
        refresh_resp = api_client.post("/api/auth/token/refresh/", {"refresh": other_device_refresh})
        assert refresh_resp.status_code == 401

    def test_failed_change_does_not_blacklist_tokens(self, api_client):
        """
        舊密碼錯誤時不得作廢任何 refresh token。
        """
        user = self._create_user_and_auth(api_client)
        outstanding = str(RefreshToken.for_user(user))
        response = api_client.put(
            self.url,
            {
                "old_password": "wrong",
                "new_password": "Bb2@zw",
                "new_password_confirm": "Bb2@zw",
            },
        )
        assert response.status_code == 400
        # 原本的 refresh 一樣可以使用
        api_client.credentials()
        refresh_resp = api_client.post("/api/auth/token/refresh/", {"refresh": outstanding})
        assert refresh_resp.status_code == 200
