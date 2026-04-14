import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestUpdatedAt:
    def test_created_with_updated_at(self):
        user = User.objects.create_user(
            email="test@example.com", username="testuser", password="Aa1!xy", is_active=True
        )
        assert user.updated_at is not None

    def test_updated_at_changes_on_save(self):
        user = User.objects.create_user(
            email="test@example.com", username="testuser", password="Aa1!xy", is_active=True
        )
        original = user.updated_at
        user.username = "changed"
        user.save()
        user.refresh_from_db()
        assert user.updated_at > original


@pytest.mark.django_db
class TestPhone:
    def test_register_without_phone(self, api_client):
        data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "Aa1!xy",
            "password_confirm": "Aa1!xy",
        }
        response = api_client.post("/api/auth/register/", data)
        assert response.status_code == 201
        user = User.objects.get(email="test@example.com")
        # phone 預設為 null（非空字串）
        assert user.phone in (None, "")

    def test_valid_international_phone(self):
        user = User.objects.create_user(
            email="test@example.com", username="testuser", password="Aa1!xy", is_active=True
        )
        user.phone = "+886912345678"
        user.full_clean()
        user.save()
        user.refresh_from_db()
        assert str(user.phone) == "+886912345678"

    def test_invalid_phone(self):
        from django.core.exceptions import ValidationError

        user = User.objects.create_user(
            email="test@example.com", username="testuser", password="Aa1!xy", is_active=True
        )
        user.phone = "12345"
        with pytest.raises(ValidationError):
            user.full_clean()


@pytest.mark.django_db
class TestProfilePhone:
    def _auth(self, api_client, user):
        from rest_framework_simplejwt.tokens import RefreshToken

        token = RefreshToken.for_user(user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")

    def test_get_profile_includes_phone(self, api_client):
        user = User.objects.create_user(
            email="test@example.com", username="testuser", password="Aa1!xy", is_active=True
        )
        self._auth(api_client, user)
        response = api_client.get("/api/members/me/")
        assert response.status_code == 200
        assert "phone" in response.data

    def test_update_phone(self, api_client):
        user = User.objects.create_user(
            email="test@example.com", username="testuser", password="Aa1!xy", is_active=True
        )
        self._auth(api_client, user)
        response = api_client.patch(
            "/api/members/me/",
            {"phone": "+886912345678"},
        )
        assert response.status_code == 200
        assert response.data["phone"] == "+886912345678"
