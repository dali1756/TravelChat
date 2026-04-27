import asyncio

import pytest
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth import get_user_model
from rest_framework.exceptions import PermissionDenied, ValidationError

from chats.models import ChatRoom, ChatRoomMember, Message
from chats.services import mark_room_read

User = get_user_model()


def _make_user(suffix):
    return User.objects.create_user(
        email=f"{suffix}@test.com",
        username=suffix,
        password="Aa1!xy",
        is_active=True,
    )


def _make_direct_room(user_a, user_b):
    direct_key = ChatRoom.make_direct_key(user_a.id, user_b.id)
    room = ChatRoom.objects.create(
        room_type=ChatRoom.RoomType.DIRECT,
        direct_key=direct_key,
        created_by=user_a,
    )
    ChatRoomMember.objects.create(room=room, user=user_a)
    ChatRoomMember.objects.create(room=room, user=user_b)
    return room


@pytest.mark.django_db
class TestMarkRoomReadBehavior:
    def test_mark_to_specific_message_advances(self):
        a = _make_user("a")
        b = _make_user("b")
        room = _make_direct_room(a, b)
        msg = Message.objects.create(room=room, sender=b, content="hi")

        result = mark_room_read(room=room, user=a, message_id=msg.id)

        assert result.advanced is True
        assert result.last_read_message_id == msg.id
        member = ChatRoomMember.objects.get(room=room, user=a)
        assert member.last_read_message_id == msg.id

    def test_mark_without_message_id_uses_latest(self):
        a = _make_user("a")
        b = _make_user("b")
        room = _make_direct_room(a, b)
        Message.objects.create(room=room, sender=b, content="m1")
        latest = Message.objects.create(room=room, sender=b, content="m2")

        result = mark_room_read(room=room, user=a, message_id=None)

        assert result.advanced is True
        assert result.last_read_message_id == latest.id

    def test_mark_without_message_id_when_room_empty(self):
        a = _make_user("a")
        b = _make_user("b")
        room = _make_direct_room(a, b)

        result = mark_room_read(room=room, user=a, message_id=None)

        assert result.advanced is False
        assert result.last_read_message_id is None

    def test_mark_does_not_advance_backwards(self):
        a = _make_user("a")
        b = _make_user("b")
        room = _make_direct_room(a, b)
        m1 = Message.objects.create(room=room, sender=b, content="m1")
        m2 = Message.objects.create(room=room, sender=b, content="m2")
        mark_room_read(room=room, user=a, message_id=m2.id)

        result = mark_room_read(room=room, user=a, message_id=m1.id)

        assert result.advanced is False
        member = ChatRoomMember.objects.get(room=room, user=a)
        assert member.last_read_message_id == m2.id

    def test_mark_same_message_again_does_not_advance(self):
        a = _make_user("a")
        b = _make_user("b")
        room = _make_direct_room(a, b)
        msg = Message.objects.create(room=room, sender=b, content="hi")
        mark_room_read(room=room, user=a, message_id=msg.id)

        result = mark_room_read(room=room, user=a, message_id=msg.id)

        assert result.advanced is False

    def test_mark_with_message_from_other_room_raises(self):
        a = _make_user("a")
        b = _make_user("b")
        c = _make_user("c")
        room1 = _make_direct_room(a, b)
        room2 = _make_direct_room(a, c)
        other_msg = Message.objects.create(room=room2, sender=c, content="other")

        with pytest.raises(ValidationError):
            mark_room_read(room=room1, user=a, message_id=other_msg.id)

        member = ChatRoomMember.objects.get(room=room1, user=a)
        assert member.last_read_message_id is None

    def test_mark_by_non_member_raises(self):
        a = _make_user("a")
        b = _make_user("b")
        outsider = _make_user("c")
        room = _make_direct_room(a, b)
        msg = Message.objects.create(room=room, sender=a, content="hi")

        with pytest.raises(PermissionDenied):
            mark_room_read(room=room, user=outsider, message_id=msg.id)


@pytest.mark.django_db(transaction=True)
class TestMarkRoomReadBroadcast:
    def test_advanced_broadcasts_message_read_to_room_group(self):
        a = _make_user("a")
        b = _make_user("b")
        room = _make_direct_room(a, b)
        msg = Message.objects.create(room=room, sender=b, content="hi")

        channel_layer = get_channel_layer()
        test_channel = "test-channel-advanced"
        async_to_sync(channel_layer.group_add)(f"chat_{room.id}", test_channel)

        async def _recv():
            return await asyncio.wait_for(channel_layer.receive(test_channel), timeout=2.0)

        try:
            result = mark_room_read(room=room, user=a, message_id=msg.id)
            event = async_to_sync(_recv)()
        finally:
            async_to_sync(channel_layer.group_discard)(f"chat_{room.id}", test_channel)

        assert result.advanced is True
        assert event["type"] == "message.read"
        assert event["room_id"] == room.id
        assert event["user_id"] == a.id
        assert event["last_read_message_id"] == msg.id
        assert "read_at" in event

    def test_not_advanced_does_not_broadcast(self):
        a = _make_user("a")
        b = _make_user("b")
        room = _make_direct_room(a, b)
        msg = Message.objects.create(room=room, sender=b, content="hi")
        mark_room_read(room=room, user=a, message_id=msg.id)

        channel_layer = get_channel_layer()
        test_channel = "test-channel-not-advanced"
        async_to_sync(channel_layer.group_add)(f"chat_{room.id}", test_channel)

        async def _try_receive():
            return await asyncio.wait_for(channel_layer.receive(test_channel), timeout=0.3)

        try:
            result = mark_room_read(room=room, user=a, message_id=msg.id)
            with pytest.raises(asyncio.TimeoutError):
                async_to_sync(_try_receive)()
        finally:
            async_to_sync(channel_layer.group_discard)(f"chat_{room.id}", test_channel)

        assert result.advanced is False
