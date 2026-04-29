import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestUserSearchAPI:
    url = "/api/members/search/"

    def _auth(self, api_client, user):
        from rest_framework_simplejwt.tokens import RefreshToken

        token = RefreshToken.for_user(user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")

    def _make_user(self, email, username, is_active=True):
        return User.objects.create_user(email=email, username=username, password="Aa1!xy", is_active=is_active)

    def test_search_returns_matching_users(self, api_client):
        me = self._make_user("me@example.com", "meuser")
        self._make_user("jet1@example.com", "jeter1")
        self._make_user("jet2@example.com", "jeter2")
        self._make_user("other@example.com", "other")
        self._auth(api_client, me)

        response = api_client.get(self.url, {"q": "jet"})

        assert response.status_code == 200
        usernames = [u["username"] for u in response.data]
        assert "jeter1" in usernames
        assert "jeter2" in usernames
        assert "other" not in usernames

    def test_search_excludes_self(self, api_client):
        me = self._make_user("me@example.com", "jetme")
        self._auth(api_client, me)

        response = api_client.get(self.url, {"q": "jet"})

        assert response.status_code == 200
        usernames = [u["username"] for u in response.data]
        assert "jetme" not in usernames

    def test_search_excludes_inactive_users(self, api_client):
        me = self._make_user("me@example.com", "meuser")
        self._make_user("inactive@example.com", "jetsleepy", is_active=False)
        self._auth(api_client, me)

        response = api_client.get(self.url, {"q": "jet"})

        assert response.status_code == 200
        usernames = [u["username"] for u in response.data]
        assert "jetsleepy" not in usernames

    def test_search_without_q_returns_empty(self, api_client):
        me = self._make_user("me@example.com", "meuser")
        self._auth(api_client, me)

        response = api_client.get(self.url)

        assert response.status_code == 200
        assert response.data == []

    def test_search_with_empty_q_returns_empty(self, api_client):
        me = self._make_user("me@example.com", "meuser")
        self._auth(api_client, me)

        response = api_client.get(self.url, {"q": ""})

        assert response.status_code == 200
        assert response.data == []

    def test_unauthenticated_returns_401(self, api_client):
        response = api_client.get(self.url, {"q": "jet"})

        assert response.status_code == 401

    def test_response_contains_only_id_and_username(self, api_client):
        me = self._make_user("me@example.com", "meuser")
        self._make_user("jet@example.com", "jetuser")
        self._auth(api_client, me)

        response = api_client.get(self.url, {"q": "jet"})

        assert response.status_code == 200
        assert len(response.data) == 1
        assert set(response.data[0].keys()) == {"id", "username"}

    def test_search_is_case_insensitive(self, api_client):
        me = self._make_user("me@example.com", "meuser")
        self._make_user("jet@example.com", "JetUser")
        self._auth(api_client, me)

        response = api_client.get(self.url, {"q": "jet"})

        assert response.status_code == 200
        usernames = [u["username"] for u in response.data]
        assert "JetUser" in usernames
