import pytest
from django.contrib.auth import get_user_model

from chats.models import ChatRoom, ChatRoomMember, Message

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
