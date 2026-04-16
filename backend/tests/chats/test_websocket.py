import pytest
from channels.db import database_sync_to_async
from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken

from chats.middleware import JWTAuthMiddleware
from chats.models import ChatRoom, ChatRoomMember, Message
from chats.routing import websocket_urlpatterns

User = get_user_model()


def _get_application():
    return JWTAuthMiddleware(URLRouter(websocket_urlpatterns))


@database_sync_to_async
def _make_user(email, username):
    return User.objects.create_user(email=email, username=username, password="Aa1!xy", is_active=True)


@database_sync_to_async
def _make_room_with_members(user_a, user_b):
    room = ChatRoom.objects.create(
        room_type=ChatRoom.RoomType.DIRECT,
        direct_key=ChatRoom.make_direct_key(user_a.id, user_b.id),
        created_by=user_a,
    )
    ChatRoomMember.objects.create(room=room, user=user_a)
    ChatRoomMember.objects.create(room=room, user=user_b)
    return room


@database_sync_to_async
def _get_message_count(room_id):
    return Message.objects.filter(room_id=room_id).count()


@database_sync_to_async
def _get_access_token(user):
    return str(AccessToken.for_user(user))


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
class TestWebSocketAuth:
    async def test_reject_without_token(self):
        user_a = await _make_user("a@test.com", "a")
        user_b = await _make_user("b@test.com", "b")
        room = await _make_room_with_members(user_a, user_b)

        communicator = WebsocketCommunicator(_get_application(), f"/ws/chat/{room.id}/")
        connected, _ = await communicator.connect()
        assert not connected
        await communicator.disconnect()

    async def test_reject_with_invalid_token(self):
        user_a = await _make_user("a@test.com", "a")
        user_b = await _make_user("b@test.com", "b")
        room = await _make_room_with_members(user_a, user_b)

        communicator = WebsocketCommunicator(_get_application(), f"/ws/chat/{room.id}/?token=invalid")
        connected, _ = await communicator.connect()
        assert not connected
        await communicator.disconnect()

    async def test_reject_non_member(self):
        user_a = await _make_user("a@test.com", "a")
        user_b = await _make_user("b@test.com", "b")
        outsider = await _make_user("outsider@test.com", "outsider")
        room = await _make_room_with_members(user_a, user_b)

        token = await _get_access_token(outsider)
        communicator = WebsocketCommunicator(_get_application(), f"/ws/chat/{room.id}/?token={token}")
        connected, _ = await communicator.connect()
        assert not connected
        await communicator.disconnect()

    async def test_accept_authenticated_member(self):
        user_a = await _make_user("a@test.com", "a")
        user_b = await _make_user("b@test.com", "b")
        room = await _make_room_with_members(user_a, user_b)

        token = await _get_access_token(user_a)
        communicator = WebsocketCommunicator(_get_application(), f"/ws/chat/{room.id}/?token={token}")
        connected, _ = await communicator.connect()
        assert connected
        await communicator.disconnect()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
class TestWebSocketMessaging:
    async def test_send_and_receive_message(self):
        user_a = await _make_user("a@test.com", "a")
        user_b = await _make_user("b@test.com", "b")
        room = await _make_room_with_members(user_a, user_b)

        token_a = await _get_access_token(user_a)
        token_b = await _get_access_token(user_b)

        comm_a = WebsocketCommunicator(_get_application(), f"/ws/chat/{room.id}/?token={token_a}")
        comm_b = WebsocketCommunicator(_get_application(), f"/ws/chat/{room.id}/?token={token_b}")

        connected_a, _ = await comm_a.connect()
        connected_b, _ = await comm_b.connect()
        assert connected_a and connected_b

        await comm_a.send_json_to({"type": "message.send", "content": "Hello from A"})

        # Both should receive the broadcast
        response_a = await comm_a.receive_json_from(timeout=5)
        response_b = await comm_b.receive_json_from(timeout=5)

        assert response_a["type"] == "message.created"
        assert response_a["message"]["content"] == "Hello from A"
        assert response_a["message"]["sender_username"] == "a"

        assert response_b["type"] == "message.created"
        assert response_b["message"]["content"] == "Hello from A"

        # Verify message persisted
        count = await _get_message_count(room.id)
        assert count == 1

        await comm_a.disconnect()
        await comm_b.disconnect()

    async def test_reject_empty_message(self):
        user_a = await _make_user("a@test.com", "a")
        user_b = await _make_user("b@test.com", "b")
        room = await _make_room_with_members(user_a, user_b)

        token = await _get_access_token(user_a)
        communicator = WebsocketCommunicator(_get_application(), f"/ws/chat/{room.id}/?token={token}")
        connected, _ = await communicator.connect()
        assert connected

        await communicator.send_json_to({"type": "message.send", "content": ""})
        response = await communicator.receive_json_from(timeout=5)
        assert response["type"] == "error"

        # Verify nothing persisted
        count = await _get_message_count(room.id)
        assert count == 0

        await communicator.disconnect()

    async def test_reject_whitespace_only_message(self):
        user_a = await _make_user("a@test.com", "a")
        user_b = await _make_user("b@test.com", "b")
        room = await _make_room_with_members(user_a, user_b)

        token = await _get_access_token(user_a)
        communicator = WebsocketCommunicator(_get_application(), f"/ws/chat/{room.id}/?token={token}")
        connected, _ = await communicator.connect()
        assert connected

        await communicator.send_json_to({"type": "message.send", "content": "   "})
        response = await communicator.receive_json_from(timeout=5)
        assert response["type"] == "error"

        count = await _get_message_count(room.id)
        assert count == 0

        await communicator.disconnect()
