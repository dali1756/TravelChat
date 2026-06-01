import pytest
from channels.db import database_sync_to_async
from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken

from chats.middleware import JWTAuthMiddleware
from chats.models import AIConversation, AIMessage
from chats.routing import websocket_urlpatterns

User = get_user_model()


def _get_application():
    return JWTAuthMiddleware(URLRouter(websocket_urlpatterns))


@database_sync_to_async
def _make_user(email, username):
    return User.objects.create_user(email=email, username=username, password="Aa1!xy", is_active=True)


@database_sync_to_async
def _make_conversation(owner):
    return AIConversation.objects.create(owner=owner)


@database_sync_to_async
def _get_access_token(user):
    return str(AccessToken.for_user(user))


@database_sync_to_async
def _message_count(conv_id, role=None):
    qs = AIMessage.objects.filter(conversation_id=conv_id)
    if role is not None:
        qs = qs.filter(role=role)
    return qs.count()


@database_sync_to_async
def _last_model_content(conv_id):
    msg = AIMessage.objects.filter(conversation_id=conv_id, role=AIMessage.Role.MODEL).last()
    if msg:
        return msg.content
    else:
        return None


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
class TestAIConsumerAuth:
    async def test_reject_without_token(self):
        owner = await _make_user("a@test.com", "a")
        conv = await _make_conversation(owner)
        communicator = WebsocketCommunicator(_get_application(), f"/ws/ai/{conv.id}/")
        connected, _ = await communicator.connect()
        assert not connected
        await communicator.disconnect()

    async def test_reject_non_owner(self):
        owner = await _make_user("a@test.com", "a")
        other = await _make_user("b@test.com", "b")
        conv = await _make_conversation(owner)
        token = await _get_access_token(other)
        communicator = WebsocketCommunicator(_get_application(), f"/ws/ai/{conv.id}/?token={token}")
        connected, _ = await communicator.connect()
        assert not connected
        await communicator.disconnect()

    async def test_accept_owner(self):
        owner = await _make_user("a@test.com", "a")
        conv = await _make_conversation(owner)
        token = await _get_access_token(owner)
        communicator = WebsocketCommunicator(_get_application(), f"/ws/ai/{conv.id}/?token={token}")
        connected, _ = await communicator.connect()
        assert connected
        await communicator.disconnect()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
class TestAIConsumerStreaming:
    async def _connect_owner(self):
        owner = await _make_user("a@test.com", "a")
        conv = await _make_conversation(owner)
        token = await _get_access_token(owner)
        communicator = WebsocketCommunicator(_get_application(), f"/ws/ai/{conv.id}/?token={token}")
        connected, _ = await communicator.connect()
        assert connected
        return communicator, conv

    async def test_stream_chunks_and_done(self):
        communicator, conv = await self._connect_owner()
        await communicator.send_json_to({"type": "ai.message", "content": "幫我規劃行程"})
        chunks = []
        done = None
        while True:
            event = await communicator.receive_json_from(timeout=5)
            if event["type"] == "ai.chunk":
                chunks.append(event["delta"])
            elif event["type"] == "ai.done":
                done = event
                break
        assert len(chunks) >= 1
        assert done is not None
        assert "message_id" in done
        full = "".join(chunks)
        assert full.strip() != ""
        # 持久化：user 與 model 訊息各一
        assert await _message_count(conv.id, AIMessage.Role.USER) == 1
        assert await _message_count(conv.id, AIMessage.Role.MODEL) == 1
        assert await _last_model_content(conv.id) == done["content"]
        await communicator.disconnect()

    async def test_reject_empty_message(self):
        communicator, conv = await self._connect_owner()
        await communicator.send_json_to({"type": "ai.message", "content": "   "})
        event = await communicator.receive_json_from(timeout=5)
        assert event["type"] == "error"
        assert await _message_count(conv.id) == 0
        await communicator.disconnect()
