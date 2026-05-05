import pytest
from django.contrib.auth import get_user_model

from chats.models import ChatRoom, ChatRoomMember

User = get_user_model()

CREATE_GROUP_URL = "/api/chats/rooms/group/"
ROOM_LIST_URL = "/api/chats/rooms/"


def _make_user(email, username):
    return User.objects.create_user(email=email, username=username, password="Aa1!xy", is_active=True)


def _auth(api_client, user):
    response = api_client.post("/api/auth/login/", {"email": user.email, "password": "Aa1!xy"})
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")


def _make_group_room(creator, name="旅遊群組", members=()):
    room = ChatRoom.objects.create(
        room_type=ChatRoom.RoomType.GROUP,
        name=name,
        created_by=creator,
    )
    ChatRoomMember.objects.create(room=room, user=creator)
    for m in members:
        ChatRoomMember.objects.create(room=room, user=m)
    return room


def _make_direct_room(user_a, user_b):
    key = ChatRoom.make_direct_key(user_a.id, user_b.id)
    room = ChatRoom.objects.create(
        room_type=ChatRoom.RoomType.DIRECT,
        direct_key=key,
        created_by=user_a,
    )
    ChatRoomMember.objects.create(room=room, user=user_a)
    ChatRoomMember.objects.create(room=room, user=user_b)
    return room


@pytest.mark.django_db
class TestRoomListAllTypes:
    def test_room_list_includes_group_rooms(self, api_client):
        a = _make_user("a@test.com", "a")
        b = _make_user("b@test.com", "b")
        direct_room = _make_direct_room(a, b)
        group_room = _make_group_room(a, "群組", members=[b])
        _auth(api_client, a)

        response = api_client.get(ROOM_LIST_URL)

        assert response.status_code == 200
        room_ids = [r["id"] for r in response.data]
        assert direct_room.id in room_ids
        assert group_room.id in room_ids

    def test_room_list_shows_room_type_field(self, api_client):
        a = _make_user("a@test.com", "a")
        b = _make_user("b@test.com", "b")
        _make_group_room(a, "群組", members=[b])
        _auth(api_client, a)

        response = api_client.get(ROOM_LIST_URL)

        assert response.status_code == 200
        types = {r["room_type"] for r in response.data}
        assert "group" in types


@pytest.mark.django_db
class TestGroupRoomCreate:
    def test_create_group_room_without_members(self, api_client):
        creator = _make_user("creator@test.com", "creator")
        _auth(api_client, creator)

        response = api_client.post(CREATE_GROUP_URL, {"name": "旅行計畫"}, format="json")

        assert response.status_code == 201
        assert response.data["room_type"] == "group"
        assert response.data["name"] == "旅行計畫"
        assert ChatRoomMember.objects.filter(room_id=response.data["id"], user=creator).exists()

    def test_create_group_room_with_initial_members(self, api_client):
        creator = _make_user("creator@test.com", "creator")
        m1 = _make_user("m1@test.com", "m1")
        m2 = _make_user("m2@test.com", "m2")
        _auth(api_client, creator)

        response = api_client.post(
            CREATE_GROUP_URL,
            {"name": "三人行", "member_ids": [m1.id, m2.id]},
            format="json",
        )

        assert response.status_code == 201
        members = ChatRoomMember.objects.filter(room_id=response.data["id"])
        assert members.count() == 3
        user_ids = set(members.values_list("user_id", flat=True))
        assert creator.id in user_ids
        assert m1.id in user_ids
        assert m2.id in user_ids

    def test_create_group_room_creator_is_auto_member(self, api_client):
        creator = _make_user("creator@test.com", "creator")
        _auth(api_client, creator)

        response = api_client.post(CREATE_GROUP_URL, {"name": "Solo"}, format="json")

        assert ChatRoomMember.objects.filter(room_id=response.data["id"], user=creator).exists()

    def test_reject_group_creation_without_name(self, api_client):
        creator = _make_user("creator@test.com", "creator")
        _auth(api_client, creator)

        response = api_client.post(CREATE_GROUP_URL, {}, format="json")

        assert response.status_code == 400

    def test_reject_group_creation_with_empty_name(self, api_client):
        creator = _make_user("creator@test.com", "creator")
        _auth(api_client, creator)

        response = api_client.post(CREATE_GROUP_URL, {"name": ""}, format="json")

        assert response.status_code == 400

    def test_reject_group_creation_with_nonexistent_member_id(self, api_client):
        creator = _make_user("creator@test.com", "creator")
        _auth(api_client, creator)

        response = api_client.post(
            CREATE_GROUP_URL,
            {"name": "群組", "member_ids": [99999]},
            format="json",
        )

        assert response.status_code == 400

    def test_reject_unauthenticated_group_creation(self, api_client):
        response = api_client.post(CREATE_GROUP_URL, {"name": "群組"}, format="json")
        assert response.status_code == 401


@pytest.mark.django_db
class TestRoomMemberList:
    def _url(self, room_id):
        return f"/api/chats/rooms/{room_id}/members/"

    def test_member_can_list_members(self, api_client):
        a = _make_user("a@test.com", "a")
        b = _make_user("b@test.com", "b")
        room = _make_group_room(a, members=[b])
        _auth(api_client, a)

        response = api_client.get(self._url(room.id))

        assert response.status_code == 200
        assert len(response.data) == 2
        user_ids = [m["user"]["id"] for m in response.data]
        assert a.id in user_ids
        assert b.id in user_ids

    def test_member_list_includes_joined_at(self, api_client):
        a = _make_user("a@test.com", "a")
        room = _make_group_room(a)
        _auth(api_client, a)

        response = api_client.get(self._url(room.id))

        assert response.status_code == 200
        assert "joined_at" in response.data[0]

    def test_non_member_cannot_list_members(self, api_client):
        a = _make_user("a@test.com", "a")
        outsider = _make_user("out@test.com", "out")
        room = _make_group_room(a)
        _auth(api_client, outsider)

        response = api_client.get(self._url(room.id))

        assert response.status_code == 403

    def test_unauthenticated_cannot_list_members(self, api_client):
        a = _make_user("a@test.com", "a")
        room = _make_group_room(a)

        response = api_client.get(self._url(room.id))

        assert response.status_code == 401


@pytest.mark.django_db
class TestRoomMemberAdd:
    def _url(self, room_id):
        return f"/api/chats/rooms/{room_id}/members/"

    def test_member_can_add_new_member(self, api_client):
        a = _make_user("a@test.com", "a")
        b = _make_user("b@test.com", "b")
        room = _make_group_room(a)
        _auth(api_client, a)

        response = api_client.post(self._url(room.id), {"user_id": b.id}, format="json")

        assert response.status_code == 201
        assert ChatRoomMember.objects.filter(room=room, user=b).exists()

    def test_adding_existing_member_is_idempotent(self, api_client):
        a = _make_user("a@test.com", "a")
        b = _make_user("b@test.com", "b")
        room = _make_group_room(a, members=[b])
        _auth(api_client, a)

        response = api_client.post(self._url(room.id), {"user_id": b.id}, format="json")

        assert response.status_code == 200
        assert ChatRoomMember.objects.filter(room=room, user=b).count() == 1

    def test_non_member_cannot_add_member(self, api_client):
        a = _make_user("a@test.com", "a")
        outsider = _make_user("out@test.com", "out")
        new_user = _make_user("new@test.com", "new")
        room = _make_group_room(a)
        _auth(api_client, outsider)

        response = api_client.post(self._url(room.id), {"user_id": new_user.id}, format="json")

        assert response.status_code == 403

    def test_cannot_add_member_to_direct_room(self, api_client):
        a = _make_user("a@test.com", "a")
        b = _make_user("b@test.com", "b")
        c = _make_user("c@test.com", "c")
        direct_room = _make_direct_room(a, b)
        _auth(api_client, a)

        response = api_client.post(self._url(direct_room.id), {"user_id": c.id}, format="json")

        assert response.status_code == 400

    def test_reject_nonexistent_user_id(self, api_client):
        a = _make_user("a@test.com", "a")
        room = _make_group_room(a)
        _auth(api_client, a)

        response = api_client.post(self._url(room.id), {"user_id": 99999}, format="json")

        assert response.status_code == 400


@pytest.mark.django_db
class TestRoomMemberRemove:
    def _url(self, room_id, user_id):
        return f"/api/chats/rooms/{room_id}/members/{user_id}/"

    def test_member_can_remove_self(self, api_client):
        a = _make_user("a@test.com", "a")
        b = _make_user("b@test.com", "b")
        room = _make_group_room(a, members=[b])
        _auth(api_client, b)

        response = api_client.delete(self._url(room.id, b.id))

        assert response.status_code == 204
        assert not ChatRoomMember.objects.filter(room=room, user=b).exists()

    def test_creator_can_remove_other_member(self, api_client):
        a = _make_user("a@test.com", "a")
        b = _make_user("b@test.com", "b")
        room = _make_group_room(a, members=[b])
        _auth(api_client, a)

        response = api_client.delete(self._url(room.id, b.id))

        assert response.status_code == 204
        assert not ChatRoomMember.objects.filter(room=room, user=b).exists()

    def test_non_creator_cannot_remove_other_member(self, api_client):
        a = _make_user("a@test.com", "a")
        b = _make_user("b@test.com", "b")
        c = _make_user("c@test.com", "c")
        room = _make_group_room(a, members=[b, c])
        _auth(api_client, b)

        response = api_client.delete(self._url(room.id, c.id))

        assert response.status_code == 403
        assert ChatRoomMember.objects.filter(room=room, user=c).exists()

    def test_non_member_cannot_remove_anyone(self, api_client):
        a = _make_user("a@test.com", "a")
        b = _make_user("b@test.com", "b")
        outsider = _make_user("out@test.com", "out")
        room = _make_group_room(a, members=[b])
        _auth(api_client, outsider)

        response = api_client.delete(self._url(room.id, b.id))

        assert response.status_code == 403

    def test_cannot_remove_from_direct_room(self, api_client):
        a = _make_user("a@test.com", "a")
        b = _make_user("b@test.com", "b")
        direct_room = _make_direct_room(a, b)
        _auth(api_client, a)

        response = api_client.delete(self._url(direct_room.id, b.id))

        assert response.status_code == 400
