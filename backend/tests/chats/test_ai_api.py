import pytest
from django.contrib.auth import get_user_model

from chats.models import AIConversation, AIMessage

User = get_user_model()


def _make_user(email, username):
    return User.objects.create_user(email=email, username=username, password="Aa1!xy", is_active=True)


def _auth(api_client, user):
    response = api_client.post("/api/auth/login/", {"email": user.email, "password": "Aa1!xy"})
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")


@pytest.mark.django_db
class TestAIConversationCreate:
    url = "/api/chats/ai/conversations/"

    def test_create_conversation(self, api_client):
        user = _make_user("a@test.com", "a")
        _auth(api_client, user)
        response = api_client.post(self.url, {"title": "東京三日遊"})
        assert response.status_code == 201
        assert response.data["title"] == "東京三日遊"
        conv = AIConversation.objects.get(id=response.data["id"])
        assert conv.owner == user

    def test_create_requires_auth(self, api_client):
        response = api_client.post(self.url, {})
        assert response.status_code == 401


@pytest.mark.django_db
class TestAIConversationList:
    url = "/api/chats/ai/conversations/"

    def test_lists_only_own_conversations(self, api_client):
        user = _make_user("a@test.com", "a")
        other = _make_user("b@test.com", "b")
        AIConversation.objects.create(owner=user, title="mine")
        AIConversation.objects.create(owner=other, title="theirs")
        _auth(api_client, user)
        response = api_client.get(self.url)
        assert response.status_code == 200
        titles = [c["title"] for c in response.data]
        assert "mine" in titles
        assert "theirs" not in titles

    def test_list_requires_auth(self, api_client):
        response = api_client.get(self.url)
        assert response.status_code == 401


@pytest.mark.django_db
class TestAIConversationMessages:
    def _url(self, conv_id):
        return f"/api/chats/ai/conversations/{conv_id}/messages/"

    def test_returns_messages_in_order(self, api_client):
        user = _make_user("a@test.com", "a")
        conv = AIConversation.objects.create(owner=user)
        AIMessage.objects.create(conversation=conv, role=AIMessage.Role.USER, content="問題")
        AIMessage.objects.create(conversation=conv, role=AIMessage.Role.MODEL, content="回答")
        _auth(api_client, user)
        response = api_client.get(self._url(conv.id))
        assert response.status_code == 200
        assert [m["role"] for m in response.data] == ["user", "model"]
        assert [m["content"] for m in response.data] == ["問題", "回答"]

    def test_non_owner_cannot_access(self, api_client):
        owner = _make_user("a@test.com", "a")
        other = _make_user("b@test.com", "b")
        conv = AIConversation.objects.create(owner=owner)
        AIMessage.objects.create(conversation=conv, role=AIMessage.Role.USER, content="secret")
        _auth(api_client, other)
        response = api_client.get(self._url(conv.id))
        assert response.status_code in (403, 404)

    def test_requires_auth(self, api_client):
        owner = _make_user("a@test.com", "a")
        conv = AIConversation.objects.create(owner=owner)
        response = api_client.get(self._url(conv.id))
        assert response.status_code == 401
