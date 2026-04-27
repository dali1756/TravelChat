import pytest
from django.contrib.auth import get_user_model

from chats.models import ChatRoom, ChatRoomMember, Message


def _make_room(user_a, user_b):
    direct_key = ChatRoom.make_direct_key(user_a.id, user_b.id)
    room = ChatRoom.objects.create(
        room_type=ChatRoom.RoomType.DIRECT,
        direct_key=direct_key,
        created_by=user_a,
    )
    ChatRoomMember.objects.create(room=room, user=user_a)
    ChatRoomMember.objects.create(room=room, user=user_b)
    return room


User = get_user_model()


def _auth(api_client, user):
    response = api_client.post("/api/auth/login/", {"email": user.email, "password": "Aa1!xy"})
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")


def _make_user(email, username):
    return User.objects.create_user(email=email, username=username, password="Aa1!xy", is_active=True)


@pytest.mark.django_db
class TestDirectRoomCreate:
    url = "/api/chats/rooms/direct/"

    def test_create_direct_room(self, api_client):
        user_a = _make_user("a@test.com", "a")
        user_b = _make_user("b@test.com", "b")
        _auth(api_client, user_a)
        response = api_client.post(self.url, {"peer_user_id": user_b.id})
        assert response.status_code == 201
        assert response.data["room_type"] == "direct"
        assert response.data["peer"]["id"] == user_b.id
        assert response.data["peer"]["username"] == "b"

    def test_duplicate_room_reuse(self, api_client):
        user_a = _make_user("a@test.com", "a")
        user_b = _make_user("b@test.com", "b")
        _auth(api_client, user_a)
        r1 = api_client.post(self.url, {"peer_user_id": user_b.id})
        r2 = api_client.post(self.url, {"peer_user_id": user_b.id})
        assert r1.data["id"] == r2.data["id"]

    def test_reject_self_chat(self, api_client):
        user_a = _make_user("a@test.com", "a")
        _auth(api_client, user_a)
        response = api_client.post(self.url, {"peer_user_id": user_a.id})
        assert response.status_code == 400

    def test_reject_unknown_peer(self, api_client):
        user_a = _make_user("a@test.com", "a")
        _auth(api_client, user_a)
        response = api_client.post(self.url, {"peer_user_id": 99999})
        assert response.status_code == 400

    def test_reject_unauthenticated(self, api_client):
        response = api_client.post(self.url, {"peer_user_id": 1})
        assert response.status_code == 401

    def test_both_directions_return_same_room(self, api_client):
        user_a = _make_user("a@test.com", "a")
        user_b = _make_user("b@test.com", "b")

        _auth(api_client, user_a)
        r1 = api_client.post(self.url, {"peer_user_id": user_b.id})

        _auth(api_client, user_b)
        r2 = api_client.post(self.url, {"peer_user_id": user_a.id})

        assert r1.data["id"] == r2.data["id"]


@pytest.mark.django_db
class TestRoomList:
    url = "/api/chats/rooms/"

    def test_list_only_own_rooms(self, api_client):
        user_a = _make_user("a@test.com", "a")
        user_b = _make_user("b@test.com", "b")
        user_c = _make_user("c@test.com", "c")

        # a-b room
        room_ab = ChatRoom.objects.create(
            room_type=ChatRoom.RoomType.DIRECT,
            direct_key=ChatRoom.make_direct_key(user_a.id, user_b.id),
            created_by=user_a,
        )
        ChatRoomMember.objects.create(room=room_ab, user=user_a)
        ChatRoomMember.objects.create(room=room_ab, user=user_b)

        # b-c room
        room_bc = ChatRoom.objects.create(
            room_type=ChatRoom.RoomType.DIRECT,
            direct_key=ChatRoom.make_direct_key(user_b.id, user_c.id),
            created_by=user_b,
        )
        ChatRoomMember.objects.create(room=room_bc, user=user_b)
        ChatRoomMember.objects.create(room=room_bc, user=user_c)

        _auth(api_client, user_a)
        response = api_client.get(self.url)
        assert response.status_code == 200
        room_ids = [r["id"] for r in response.data]
        assert room_ab.id in room_ids
        assert room_bc.id not in room_ids

    def test_reject_unauthenticated(self, api_client):
        response = api_client.get(self.url)
        assert response.status_code == 401


@pytest.mark.django_db
class TestRoomListUnreadCount:
    url = "/api/chats/rooms/"

    def test_unread_count_when_never_read(self, api_client):
        a = _make_user("a@test.com", "a")
        b = _make_user("b@test.com", "b")
        room = _make_room(a, b)
        Message.objects.create(room=room, sender=b, content="m1")
        Message.objects.create(room=room, sender=b, content="m2")
        _auth(api_client, a)

        response = api_client.get(self.url)

        assert response.status_code == 200
        room_data = next(r for r in response.data if r["id"] == room.id)
        assert room_data["unread_count"] == 2

    def test_unread_count_zero_after_reading_latest(self, api_client):
        a = _make_user("a@test.com", "a")
        b = _make_user("b@test.com", "b")
        room = _make_room(a, b)
        Message.objects.create(room=room, sender=b, content="m1")
        latest = Message.objects.create(room=room, sender=b, content="m2")
        member = ChatRoomMember.objects.get(room=room, user=a)
        member.last_read_message = latest
        member.save()
        _auth(api_client, a)

        response = api_client.get(self.url)

        room_data = next(r for r in response.data if r["id"] == room.id)
        assert room_data["unread_count"] == 0

    def test_own_messages_not_counted_as_unread(self, api_client):
        a = _make_user("a@test.com", "a")
        b = _make_user("b@test.com", "b")
        room = _make_room(a, b)
        Message.objects.create(room=room, sender=a, content="my own m1")
        Message.objects.create(room=room, sender=a, content="my own m2")
        _auth(api_client, a)

        response = api_client.get(self.url)

        room_data = next(r for r in response.data if r["id"] == room.id)
        assert room_data["unread_count"] == 0

    def test_unread_counts_independent_per_room(self, api_client):
        a = _make_user("a@test.com", "a")
        b = _make_user("b@test.com", "b")
        c = _make_user("c@test.com", "c")
        room_ab = _make_room(a, b)
        room_ac = _make_room(a, c)
        Message.objects.create(room=room_ab, sender=b, content="ab1")
        Message.objects.create(room=room_ab, sender=b, content="ab2")
        Message.objects.create(room=room_ac, sender=c, content="ac1")
        _auth(api_client, a)

        response = api_client.get(self.url)

        by_id = {r["id"]: r for r in response.data}
        assert by_id[room_ab.id]["unread_count"] == 2
        assert by_id[room_ac.id]["unread_count"] == 1

    def test_room_list_no_n_plus_1(self, api_client, django_assert_max_num_queries):
        a = _make_user("a@test.com", "a")
        peers = [_make_user(f"p{i}@test.com", f"p{i}") for i in range(5)]
        for peer in peers:
            room = _make_room(a, peer)
            Message.objects.create(room=room, sender=peer, content="m1")
            Message.objects.create(room=room, sender=peer, content="m2")
        _auth(api_client, a)

        with django_assert_max_num_queries(15):
            response = api_client.get(self.url)
            assert response.status_code == 200
            assert len(response.data) == 5


@pytest.mark.django_db
class TestMessageHistory:
    def _setup_room(self):
        user_a = _make_user("a@test.com", "a")
        user_b = _make_user("b@test.com", "b")
        room = ChatRoom.objects.create(
            room_type=ChatRoom.RoomType.DIRECT,
            direct_key=ChatRoom.make_direct_key(user_a.id, user_b.id),
            created_by=user_a,
        )
        ChatRoomMember.objects.create(room=room, user=user_a)
        ChatRoomMember.objects.create(room=room, user=user_b)
        Message.objects.create(room=room, sender=user_a, content="Hello")
        Message.objects.create(room=room, sender=user_b, content="Hi")
        return user_a, user_b, room

    def test_member_can_read_history(self, api_client):
        user_a, user_b, room = self._setup_room()
        _auth(api_client, user_a)
        response = api_client.get(f"/api/chats/rooms/{room.id}/messages/")
        assert response.status_code == 200
        assert len(response.data) == 2
        assert response.data[0]["content"] == "Hello"
        assert response.data[1]["content"] == "Hi"

    def test_non_member_rejected(self, api_client):
        user_a, user_b, room = self._setup_room()
        outsider = _make_user("outsider@test.com", "outsider")
        _auth(api_client, outsider)
        response = api_client.get(f"/api/chats/rooms/{room.id}/messages/")
        assert response.status_code == 403

    def test_reject_unauthenticated(self, api_client):
        user_a, user_b, room = self._setup_room()
        response = api_client.get(f"/api/chats/rooms/{room.id}/messages/")
        assert response.status_code == 401


@pytest.mark.django_db
class TestMarkRoomReadAPI:
    def _url(self, room_id):
        return f"/api/chats/rooms/{room_id}/read/"

    def test_member_marks_specific_message(self, api_client):
        a = _make_user("a@test.com", "a")
        b = _make_user("b@test.com", "b")
        room = _make_room(a, b)
        msg = Message.objects.create(room=room, sender=b, content="hi")
        _auth(api_client, a)

        response = api_client.post(self._url(room.id), {"message_id": msg.id}, format="json")

        assert response.status_code == 200
        assert response.data["advanced"] is True
        assert response.data["last_read_message_id"] == msg.id

    def test_member_marks_latest_when_no_message_id(self, api_client):
        a = _make_user("a@test.com", "a")
        b = _make_user("b@test.com", "b")
        room = _make_room(a, b)
        Message.objects.create(room=room, sender=b, content="m1")
        latest = Message.objects.create(room=room, sender=b, content="m2")
        _auth(api_client, a)

        response = api_client.post(self._url(room.id), {}, format="json")

        assert response.status_code == 200
        assert response.data["advanced"] is True
        assert response.data["last_read_message_id"] == latest.id

    def test_non_member_rejected(self, api_client):
        a = _make_user("a@test.com", "a")
        b = _make_user("b@test.com", "b")
        outsider = _make_user("c@test.com", "c")
        room = _make_room(a, b)
        msg = Message.objects.create(room=room, sender=a, content="hi")
        _auth(api_client, outsider)

        response = api_client.post(self._url(room.id), {"message_id": msg.id}, format="json")

        assert response.status_code in (403, 404)

    def test_unauthenticated_rejected(self, api_client):
        a = _make_user("a@test.com", "a")
        b = _make_user("b@test.com", "b")
        room = _make_room(a, b)

        response = api_client.post(self._url(room.id), {}, format="json")

        assert response.status_code == 401

    def test_message_id_from_other_room_rejected(self, api_client):
        a = _make_user("a@test.com", "a")
        b = _make_user("b@test.com", "b")
        c = _make_user("c@test.com", "c")
        room1 = _make_room(a, b)
        room2 = _make_room(a, c)
        other_msg = Message.objects.create(room=room2, sender=c, content="other")
        _auth(api_client, a)

        response = api_client.post(self._url(room1.id), {"message_id": other_msg.id}, format="json")

        assert response.status_code == 400

    def test_backwards_request_returns_advanced_false(self, api_client):
        a = _make_user("a@test.com", "a")
        b = _make_user("b@test.com", "b")
        room = _make_room(a, b)
        m1 = Message.objects.create(room=room, sender=b, content="m1")
        m2 = Message.objects.create(room=room, sender=b, content="m2")
        _auth(api_client, a)
        api_client.post(self._url(room.id), {"message_id": m2.id}, format="json")

        response = api_client.post(self._url(room.id), {"message_id": m1.id}, format="json")

        assert response.status_code == 200
        assert response.data["advanced"] is False
        assert response.data["last_read_message_id"] == m2.id
