import pytest

from trips.models import TripMember


def _list_url(trip_id):
    return f"/api/trips/{trip_id}/members/"


def _detail_url(trip_id, user_id):
    return f"/api/trips/{trip_id}/members/{user_id}/"


@pytest.mark.django_db
class TestMemberCreate:
    def test_owner_can_share_with_default_viewer_role(self, api_client, make_user, auth, make_trip):
        owner = make_user("a@test.com", "a")
        friend = make_user("b@test.com", "b")
        trip = make_trip(owner)
        auth(owner)
        response = api_client.post(_list_url(trip.id), {"user_id": friend.id})
        assert response.status_code == 201
        member = TripMember.objects.get(trip=trip, user=friend)
        assert member.role == TripMember.Role.VIEWER

    def test_owner_can_share_as_editor(self, api_client, make_user, auth, make_trip):
        owner = make_user("a@test.com", "a")
        friend = make_user("b@test.com", "b")
        trip = make_trip(owner)
        auth(owner)
        response = api_client.post(_list_url(trip.id), {"user_id": friend.id, "role": "editor"})
        assert response.status_code == 201
        assert TripMember.objects.get(trip=trip, user=friend).role == TripMember.Role.EDITOR

    def test_share_with_nonexistent_user(self, api_client, make_user, auth, make_trip):
        owner = make_user("a@test.com", "a")
        trip = make_trip(owner)
        auth(owner)
        response = api_client.post(_list_url(trip.id), {"user_id": 99999})
        assert response.status_code == 400
        assert "user_id" in response.data

    def test_share_with_existing_member(self, api_client, make_user, auth, make_trip, share_trip):
        owner = make_user("a@test.com", "a")
        friend = make_user("b@test.com", "b")
        trip = make_trip(owner)
        share_trip(trip, friend, TripMember.Role.VIEWER)
        auth(owner)
        response = api_client.post(_list_url(trip.id), {"user_id": friend.id})
        assert response.status_code == 400

    def test_share_with_self(self, api_client, make_user, auth, make_trip):
        owner = make_user("a@test.com", "a")
        trip = make_trip(owner)
        auth(owner)
        response = api_client.post(_list_url(trip.id), {"user_id": owner.id})
        assert response.status_code == 400

    def test_editor_cannot_share(self, api_client, make_user, auth, make_trip, share_trip):
        owner = make_user("a@test.com", "a")
        editor = make_user("b@test.com", "b")
        target = make_user("c@test.com", "c")
        trip = make_trip(owner)
        share_trip(trip, editor, TripMember.Role.EDITOR)
        auth(editor)
        response = api_client.post(_list_url(trip.id), {"user_id": target.id})
        assert response.status_code == 403


@pytest.mark.django_db
class TestMemberList:
    def test_participant_can_list_members(self, api_client, make_user, auth, make_trip, share_trip):
        owner = make_user("a@test.com", "a")
        viewer = make_user("b@test.com", "b")
        trip = make_trip(owner)
        share_trip(trip, viewer, TripMember.Role.VIEWER)
        auth(viewer)
        response = api_client.get(_list_url(trip.id))
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["user"]["username"] == "b"
        assert response.data[0]["role"] == "viewer"

    def test_non_participant_gets_404(self, api_client, make_user, auth, make_trip):
        owner = make_user("a@test.com", "a")
        outsider = make_user("b@test.com", "b")
        trip = make_trip(owner)
        auth(outsider)
        response = api_client.get(_list_url(trip.id))
        assert response.status_code == 404


@pytest.mark.django_db
class TestMemberRemove:
    def test_owner_can_remove_member(self, api_client, make_user, auth, make_trip, share_trip):
        owner = make_user("a@test.com", "a")
        member = make_user("b@test.com", "b")
        trip = make_trip(owner)
        share_trip(trip, member, TripMember.Role.VIEWER)
        auth(owner)
        response = api_client.delete(_detail_url(trip.id, member.id))
        assert response.status_code == 204
        assert not TripMember.objects.filter(trip=trip, user=member).exists()

    def test_member_can_leave_trip(self, api_client, make_user, auth, make_trip, share_trip):
        owner = make_user("a@test.com", "a")
        member = make_user("b@test.com", "b")
        trip = make_trip(owner)
        share_trip(trip, member, TripMember.Role.EDITOR)
        auth(member)
        response = api_client.delete(_detail_url(trip.id, member.id))
        assert response.status_code == 204
        assert api_client.get(f"/api/trips/{trip.id}/").status_code == 404

    def test_member_cannot_remove_other_member(self, api_client, make_user, auth, make_trip, share_trip):
        owner = make_user("a@test.com", "a")
        member = make_user("b@test.com", "b")
        other = make_user("c@test.com", "c")
        trip = make_trip(owner)
        share_trip(trip, member, TripMember.Role.EDITOR)
        share_trip(trip, other, TripMember.Role.VIEWER)
        auth(member)
        response = api_client.delete(_detail_url(trip.id, other.id))
        assert response.status_code == 403
        assert TripMember.objects.filter(trip=trip, user=other).exists()

    def test_remove_non_member(self, api_client, make_user, auth, make_trip):
        owner = make_user("a@test.com", "a")
        stranger = make_user("b@test.com", "b")
        trip = make_trip(owner)
        auth(owner)
        response = api_client.delete(_detail_url(trip.id, stranger.id))
        assert response.status_code == 404
