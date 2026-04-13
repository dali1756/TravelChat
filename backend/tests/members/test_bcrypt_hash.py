import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestBcryptHash:
    def test_password_stored_as_bcrypt(self):
        user = User.objects.create_user(email="test@example.com", username="testuser", password="Aa1!xy")
        user.refresh_from_db()
        assert user.password.startswith("bcrypt_sha256$")
