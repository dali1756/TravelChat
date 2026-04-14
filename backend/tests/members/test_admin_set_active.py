import pytest
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


def _auth(api_client, user):
    access = str(RefreshToken.for_user(user).access_token)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")


@pytest.mark.django_db
class TestAdminSetUserActive:
    def _url(self, user_id):
        return f"/api/admin/members/{user_id}/active/"

    def test_unauthenticated_gets_401(self, api_client):
        target = User.objects.create_user(
            email="target@example.com", username="target", password="Aa1!xy", is_active=True
        )
        response = api_client.patch(self._url(target.id), {"is_active": False})
        assert response.status_code == 401

    def test_non_staff_gets_403(self, api_client):
        caller = User.objects.create_user(
            email="caller@example.com", username="caller", password="Aa1!xy", is_active=True
        )
        target = User.objects.create_user(
            email="target@example.com", username="target", password="Aa1!xy", is_active=True
        )
        _auth(api_client, caller)
        response = api_client.patch(self._url(target.id), {"is_active": False})
        assert response.status_code == 403

    def test_staff_can_deactivate_and_blacklists_tokens(self, api_client):
        staff = User.objects.create_user(
            email="staff@example.com",
            username="staff",
            password="Aa1!xy",
            is_active=True,
            is_staff=True,
        )
        target = User.objects.create_user(
            email="target@example.com", username="target", password="Aa1!xy", is_active=True
        )
        target_refresh = str(RefreshToken.for_user(target))

        _auth(api_client, staff)
        response = api_client.patch(self._url(target.id), {"is_active": False})
        assert response.status_code == 200

        target.refresh_from_db()
        assert target.is_active is False

        # target 的 refresh token 應已被 blacklist
        api_client.credentials()
        refresh_resp = api_client.post("/api/auth/token/refresh/", {"refresh": target_refresh})
        assert refresh_resp.status_code == 401

    def test_staff_can_activate(self, api_client):
        staff = User.objects.create_user(
            email="staff@example.com",
            username="staff",
            password="Aa1!xy",
            is_active=True,
            is_staff=True,
        )
        target = User.objects.create_user(
            email="target@example.com", username="target", password="Aa1!xy", is_active=False
        )
        _auth(api_client, staff)
        response = api_client.patch(self._url(target.id), {"is_active": True})
        assert response.status_code == 200

        target.refresh_from_db()
        assert target.is_active is True

    def test_nonexistent_user_404(self, api_client):
        staff = User.objects.create_user(
            email="staff@example.com",
            username="staff",
            password="Aa1!xy",
            is_active=True,
            is_staff=True,
        )
        _auth(api_client, staff)
        response = api_client.patch(self._url(999999), {"is_active": False})
        assert response.status_code == 404
