import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestSoftDeleteMixin:
    def test_soft_delete_sets_deleted_at(self):
        user = User.objects.create_user(
            email="test@example.com", username="testuser", password="Aa1!xy", is_active=True
        )
        assert user.deleted_at is None
        user.soft_delete()
        user.refresh_from_db()
        assert user.deleted_at is not None

    def test_restore_clears_deleted_at(self):
        user = User.objects.create_user(
            email="test@example.com", username="testuser", password="Aa1!xy", is_active=True
        )
        user.soft_delete()
        user.restore()
        user.refresh_from_db()
        assert user.deleted_at is None

    def test_objects_excludes_soft_deleted(self):
        user = User.objects.create_user(
            email="test@example.com", username="testuser", password="Aa1!xy", is_active=True
        )
        user.soft_delete()
        assert User.objects.filter(email="test@example.com").count() == 0

    def test_all_objects_includes_soft_deleted(self):
        user = User.objects.create_user(
            email="test@example.com", username="testuser", password="Aa1!xy", is_active=True
        )
        user.soft_delete()
        assert User.all_objects.filter(email="test@example.com").count() == 1


@pytest.mark.django_db
class TestUserModelFields:
    def test_date_joined_auto_set(self):
        user = User.objects.create_user(
            email="test@example.com", username="testuser", password="Aa1!xy", is_active=True
        )
        assert user.date_joined is not None

    def test_last_login_default_null(self):
        user = User.objects.create_user(
            email="test@example.com", username="testuser", password="Aa1!xy", is_active=True
        )
        assert user.last_login is None


@pytest.mark.django_db
class TestLoginUpdatesLastLogin:
    def test_login_updates_last_login(self, api_client):
        User.objects.create_user(email="test@example.com", username="testuser", password="Aa1!xy", is_active=True)
        response = api_client.post("/api/auth/login/", {"email": "test@example.com", "password": "Aa1!xy"})
        assert response.status_code == 200
        user = User.objects.get(email="test@example.com")
        assert user.last_login is not None


@pytest.mark.django_db
class TestUserSoftDeleteQuery:
    def test_soft_deleted_user_excluded_from_default_query(self):
        user = User.objects.create_user(
            email="test@example.com", username="testuser", password="Aa1!xy", is_active=True
        )
        user.soft_delete()
        assert not User.objects.filter(email="test@example.com").exists()
        assert User.all_objects.filter(email="test@example.com").exists()
