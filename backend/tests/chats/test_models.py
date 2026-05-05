import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError

from chats.models import ChatRoom, ChatRoomMember, Message

User = get_user_model()


@pytest.mark.django_db
class TestChatRoomModel:
    def test_group_room_type_exists(self):
        assert ChatRoom.RoomType.GROUP == "group"

    def test_group_room_can_be_created(self):
        user = User.objects.create_user(email="a@test.com", username="a", password="Aa1!xy", is_active=True)
        room = ChatRoom.objects.create(
            room_type=ChatRoom.RoomType.GROUP,
            name="Travel Crew",
            created_by=user,
        )
        assert room.room_type == "group"
        assert room.name == "Travel Crew"

    def test_make_direct_key_sorted(self):
        assert ChatRoom.make_direct_key(5, 3) == "3:5"
        assert ChatRoom.make_direct_key(1, 10) == "1:10"

    def test_direct_key_unique_constraint(self):
        user_a = User.objects.create_user(email="a@test.com", username="a", password="Aa1!xy", is_active=True)
        user_b = User.objects.create_user(email="b@test.com", username="b", password="Aa1!xy", is_active=True)
        key = ChatRoom.make_direct_key(user_a.id, user_b.id)
        ChatRoom.objects.create(room_type=ChatRoom.RoomType.DIRECT, direct_key=key, created_by=user_a)
        with pytest.raises(IntegrityError):
            ChatRoom.objects.create(room_type=ChatRoom.RoomType.DIRECT, direct_key=key, created_by=user_b)

    def test_room_str_with_name(self):
        user = User.objects.create_user(email="a@test.com", username="a", password="Aa1!xy", is_active=True)
        room = ChatRoom.objects.create(room_type=ChatRoom.RoomType.DIRECT, name="Test Room", created_by=user)
        assert str(room) == "Test Room"

    def test_room_str_without_name(self):
        user = User.objects.create_user(email="a@test.com", username="a", password="Aa1!xy", is_active=True)
        room = ChatRoom.objects.create(room_type=ChatRoom.RoomType.DIRECT, created_by=user)
        assert "direct" in str(room).lower()


@pytest.mark.django_db
class TestChatRoomMemberModel:
    def test_create_membership(self):
        user = User.objects.create_user(email="a@test.com", username="a", password="Aa1!xy", is_active=True)
        room = ChatRoom.objects.create(room_type=ChatRoom.RoomType.DIRECT, created_by=user)
        member = ChatRoomMember.objects.create(room=room, user=user)
        assert member.room == room
        assert member.user == user

    def test_unique_membership(self):
        user = User.objects.create_user(email="a@test.com", username="a", password="Aa1!xy", is_active=True)
        room = ChatRoom.objects.create(room_type=ChatRoom.RoomType.DIRECT, created_by=user)
        ChatRoomMember.objects.create(room=room, user=user)
        with pytest.raises(IntegrityError):
            ChatRoomMember.objects.create(room=room, user=user)

    def test_last_read_message_defaults_to_none(self):
        user = User.objects.create_user(email="a@test.com", username="a", password="Aa1!xy", is_active=True)
        room = ChatRoom.objects.create(room_type=ChatRoom.RoomType.DIRECT, created_by=user)
        member = ChatRoomMember.objects.create(room=room, user=user)
        assert member.last_read_message is None

    def test_last_read_message_can_point_to_message(self):
        user = User.objects.create_user(email="a@test.com", username="a", password="Aa1!xy", is_active=True)
        room = ChatRoom.objects.create(room_type=ChatRoom.RoomType.DIRECT, created_by=user)
        member = ChatRoomMember.objects.create(room=room, user=user)
        msg = Message.objects.create(room=room, sender=user, content="hello")
        member.last_read_message = msg
        member.save()
        member.refresh_from_db()
        assert member.last_read_message_id == msg.id

    def test_last_read_message_set_null_on_message_delete(self):
        user = User.objects.create_user(email="a@test.com", username="a", password="Aa1!xy", is_active=True)
        room = ChatRoom.objects.create(room_type=ChatRoom.RoomType.DIRECT, created_by=user)
        member = ChatRoomMember.objects.create(room=room, user=user)
        msg = Message.objects.create(room=room, sender=user, content="hello")
        member.last_read_message = msg
        member.save()
        msg.delete()
        member.refresh_from_db()
        assert member.last_read_message is None


@pytest.mark.django_db
class TestMessageModel:
    def test_create_message(self):
        user = User.objects.create_user(email="a@test.com", username="a", password="Aa1!xy", is_active=True)
        room = ChatRoom.objects.create(room_type=ChatRoom.RoomType.DIRECT, created_by=user)
        msg = Message.objects.create(room=room, sender=user, content="Hello")
        assert msg.content == "Hello"
        assert msg.message_type == Message.MessageType.TEXT
        assert msg.created_at is not None

    def test_messages_ordered_by_created_at(self):
        user = User.objects.create_user(email="a@test.com", username="a", password="Aa1!xy", is_active=True)
        room = ChatRoom.objects.create(room_type=ChatRoom.RoomType.DIRECT, created_by=user)
        msg1 = Message.objects.create(room=room, sender=user, content="First")
        msg2 = Message.objects.create(room=room, sender=user, content="Second")
        messages = list(Message.objects.filter(room=room))
        assert messages[0].id == msg1.id
        assert messages[1].id == msg2.id
