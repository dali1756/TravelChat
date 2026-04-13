import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestSoftDeleteMixin:
    def test_soft_delete_sets_deleted_at(self):
        user = User.objects.create_user(email="test@example.com", username="testuser", password="Aa1!xy")
        assert user.deleted_at is None
        user.soft_delete()
        user.refresh_from_db()
        assert user.deleted_at is not None

    def test_restore_clears_deleted_at(self):
        user = User.objects.create_user(email="test@example.com", username="testuser", password="Aa1!xy")
        user.soft_delete()
        user.restore()
        user.refresh_from_db()
        assert user.deleted_at is None

    def test_objects_excludes_soft_deleted(self):
        user = User.objects.create_user(email="test@example.com", username="testuser", password="Aa1!xy")
        user.soft_delete()
        assert User.objects.filter(email="test@example.com").count() == 0

    def test_all_objects_includes_soft_deleted(self):
        user = User.objects.create_user(email="test@example.com", username="testuser", password="Aa1!xy")
        user.soft_delete()
        assert User.all_objects.filter(email="test@example.com").count() == 1


@pytest.mark.django_db
class TestUserModelFields:
    def test_created_at_auto_set(self):
        user = User.objects.create_user(email="test@example.com", username="testuser", password="Aa1!xy")
        assert user.created_at is not None

    def test_last_login_time_default_null(self):
        user = User.objects.create_user(email="test@example.com", username="testuser", password="Aa1!xy")
        assert user.last_login_time is None


@pytest.mark.django_db
class TestLoginUpdatesLastLoginTime:
    def test_login_updates_last_login_time(self, api_client):
        User.objects.create_user(email="test@example.com", username="testuser", password="Aa1!xy")
        response = api_client.post("/api/auth/login/", {"email": "test@example.com", "password": "Aa1!xy"})
        assert response.status_code == 200
        user = User.objects.get(email="test@example.com")
        assert user.last_login_time is not None


@pytest.mark.django_db
class TestUserSoftDeleteQuery:
    def test_soft_deleted_user_excluded_from_default_query(self):
        user = User.objects.create_user(email="test@example.com", username="testuser", password="Aa1!xy")
        user.soft_delete()
        assert not User.objects.filter(email="test@example.com").exists()
        assert User.all_objects.filter(email="test@example.com").exists()
