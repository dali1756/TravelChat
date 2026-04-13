from datetime import timedelta

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()


class TestSimpleJWTSettings:
    def test_access_token_lifetime_15_minutes(self):
        assert settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"] == timedelta(minutes=15)

    def test_refresh_token_lifetime_7_days(self):
        assert settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"] == timedelta(days=7)

    def test_refresh_rotation_enabled(self):
        assert settings.SIMPLE_JWT["ROTATE_REFRESH_TOKENS"] is True

    def test_blacklist_after_rotation_enabled(self):
        assert settings.SIMPLE_JWT["BLACKLIST_AFTER_ROTATION"] is True

    def test_token_blacklist_app_installed(self):
        assert "rest_framework_simplejwt.token_blacklist" in settings.INSTALLED_APPS


@pytest.mark.django_db
class TestRefreshRotation:
    def test_old_refresh_blacklisted_after_rotation(self, api_client):
        User.objects.create_user(email="test@example.com", username="testuser", password="Aa1!xy")
        login = api_client.post("/api/auth/login/", {"email": "test@example.com", "password": "Aa1!xy"})
        original_refresh = login.data["refresh"]

        rotation = api_client.post("/api/auth/token/refresh/", {"refresh": original_refresh})
        assert rotation.status_code == 200
        assert "refresh" in rotation.data  # rotation enabled：會回傳新 refresh
        new_refresh = rotation.data["refresh"]
        assert new_refresh != original_refresh

        # 舊 refresh 已被 blacklist，不能再用
        reuse = api_client.post("/api/auth/token/refresh/", {"refresh": original_refresh})
        assert reuse.status_code == 401

        # 新 refresh 可正常使用
        fresh = api_client.post("/api/auth/token/refresh/", {"refresh": new_refresh})
        assert fresh.status_code == 200
