import pytest
from django.contrib.auth import get_user_model
from django.test import Client

User = get_user_model()


@pytest.fixture
def admin_client(db):
    User.objects.create_superuser(email="admin@example.com", username="adminboss", password="Aa1!xy")
    client = Client()
    logged_in = client.login(email="admin@example.com", password="Aa1!xy")
    assert logged_in, "admin 未能登入 Django admin"
    return client


@pytest.mark.django_db
class TestDjangoAdminPanel:
    def test_changelist_loads(self, admin_client):
        response = admin_client.get("/admin/members/user/")
        assert response.status_code == 200

    def test_changelist_shows_expected_columns(self, admin_client):
        User.objects.create_user(email="visible@example.com", username="vis", password="Aa1!xy")
        response = admin_client.get("/admin/members/user/")
        assert response.status_code == 200
        content = response.content.decode()
        assert "visible@example.com" in content
        assert "vis" in content

    def test_add_user_page_loads(self, admin_client):
        response = admin_client.get("/admin/members/user/add/")
        assert response.status_code == 200
        content = response.content.decode()
        # add_fieldsets 必須包含 email / username / password1 / password2
        assert "email" in content.lower()
        assert "username" in content.lower()

    def test_change_user_page_loads(self, admin_client):
        user = User.objects.create_user(email="target@example.com", username="target", password="Aa1!xy")
        response = admin_client.get(f"/admin/members/user/{user.pk}/change/")
        assert response.status_code == 200
