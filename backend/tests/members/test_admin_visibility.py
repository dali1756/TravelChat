import pytest
from django.contrib.auth import authenticate, get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestPublicQueryset:
    def test_public_excludes_superuser(self):
        User.objects.create_user(email="user@example.com", username="normal", password="Aa1!xy")
        User.objects.create_superuser(email="admin@example.com", username="adminboss", password="Aa1!xy")

        public_emails = set(User.objects.public().values_list("email", flat=True))
        assert "user@example.com" in public_emails
        assert "admin@example.com" not in public_emails

    def test_public_excludes_username_admin_case_insensitive(self):
        User.objects.create_user(email="a@example.com", username="admin", password="Aa1!xy")
        User.objects.create_user(email="b@example.com", username="ADMIN", password="Aa1!xy")
        User.objects.create_user(email="c@example.com", username="AdMiN", password="Aa1!xy")
        User.objects.create_user(email="regular@example.com", username="regular", password="Aa1!xy")

        public_usernames = set(User.objects.public().values_list("username", flat=True))
        assert "regular" in public_usernames
        assert "admin" not in public_usernames
        assert "ADMIN" not in public_usernames
        assert "AdMiN" not in public_usernames

    def test_default_objects_still_contains_admin(self):
        """
        admin 必須在 User.objects，否則 authenticate() / createsuperuser 會壞掉
        """
        User.objects.create_superuser(email="admin@example.com", username="adminboss", password="Aa1!xy")
        assert User.objects.filter(email="admin@example.com").exists()


@pytest.mark.django_db
class TestAdminCanLogin:
    def test_superuser_authenticate(self):
        User.objects.create_superuser(email="admin@example.com", username="adminboss", password="Aa1!xy")
        user = authenticate(email="admin@example.com", password="Aa1!xy")
        assert user is not None
        assert user.is_superuser is True

    def test_superuser_login_endpoint(self, api_client):
        User.objects.create_superuser(email="admin@example.com", username="adminboss", password="Aa1!xy")
        response = api_client.post(
            "/api/auth/login/",
            {"email": "admin@example.com", "password": "Aa1!xy"},
        )
        assert response.status_code == 200
        assert "access" in response.data
        assert "refresh" in response.data


@pytest.mark.django_db
class TestRegisterAgainstAdminEmail:
    """
    當使用者嘗試使用 admin 相同 email 註冊時，回應必須與一般 email 衝突相同，
    不可透過差異發現 admin 存在。
    """

    def test_same_error_shape_for_admin_and_normal_collision(self, api_client):
        User.objects.create_superuser(email="admin@example.com", username="adminboss", password="Aa1!xy")
        User.objects.create_user(email="normal@example.com", username="normal", password="Aa1!xy")

        resp_admin = api_client.post(
            "/api/auth/register/",
            {
                "username": "new1",
                "email": "admin@example.com",
                "password": "Aa1!xy",
                "password_confirm": "Aa1!xy",
            },
        )
        resp_normal = api_client.post(
            "/api/auth/register/",
            {
                "username": "new2",
                "email": "normal@example.com",
                "password": "Aa1!xy",
                "password_confirm": "Aa1!xy",
            },
        )

        assert resp_admin.status_code == 400
        assert resp_normal.status_code == 400
        assert "email" in resp_admin.data
        assert "email" in resp_normal.data
        assert resp_admin.data["email"] == resp_normal.data["email"]
