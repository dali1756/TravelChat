from datetime import date

import pytest

from trips.models import Activity, Attraction, TripDay, TripMember


def _list_url(trip_id, day_id):
    return f"/api/trips/{trip_id}/days/{day_id}/activities/"


def _detail_url(trip_id, day_id, activity_id):
    return f"/api/trips/{trip_id}/days/{day_id}/activities/{activity_id}/"


@pytest.fixture
def trip_with_day(make_user, make_trip):
    owner = make_user("a@test.com", "a")
    trip = make_trip(owner)
    day = TripDay.objects.create(trip=trip, date=date(2026, 7, 1))
    return owner, trip, day


@pytest.mark.django_db
class TestActivityCreate:
    def test_create_with_attraction(self, api_client, auth, trip_with_day):
        owner, trip, day = trip_with_day
        attraction = Attraction.objects.create(name="淺草寺", created_by=owner)
        auth(owner)
        response = api_client.post(
            _list_url(trip.id, day.id),
            {"title": "參拜淺草寺", "attraction_id": attraction.id, "start_time": "09:00", "end_time": "11:00"},
        )
        assert response.status_code == 201
        assert response.data["attraction"]["name"] == "淺草寺"
        activity = Activity.objects.get(id=response.data["id"])
        assert activity.day == day
        assert activity.attraction == attraction

    def test_create_plain_text_activity(self, api_client, auth, trip_with_day):
        owner, trip, day = trip_with_day
        auth(owner)
        response = api_client.post(_list_url(trip.id, day.id), {"title": "機場集合"})
        assert response.status_code == 201
        assert response.data["attraction"] is None

    def test_end_time_before_start_time(self, api_client, auth, trip_with_day):
        owner, trip, day = trip_with_day
        auth(owner)
        response = api_client.post(
            _list_url(trip.id, day.id),
            {"title": "壞活動", "start_time": "14:00", "end_time": "10:00"},
        )
        assert response.status_code == 400
        assert "end_time" in response.data

    def test_viewer_cannot_create(self, api_client, make_user, auth, share_trip, trip_with_day):
        owner, trip, day = trip_with_day
        viewer = make_user("b@test.com", "b")
        share_trip(trip, viewer, TripMember.Role.VIEWER)
        auth(viewer)
        response = api_client.post(_list_url(trip.id, day.id), {"title": "不該成功"})
        assert response.status_code == 403

    def test_non_participant_gets_404(self, api_client, make_user, auth, trip_with_day):
        owner, trip, day = trip_with_day
        outsider = make_user("b@test.com", "b")
        auth(outsider)
        assert api_client.get(_list_url(trip.id, day.id)).status_code == 404
        assert api_client.post(_list_url(trip.id, day.id), {"title": "x"}).status_code == 404


@pytest.mark.django_db
class TestActivityList:
    def test_ordered_by_order_then_id(self, api_client, auth, trip_with_day):
        owner, trip, day = trip_with_day
        late = Activity.objects.create(day=day, title="晚餐", order=2)
        early = Activity.objects.create(day=day, title="淺草寺", order=1)
        auth(owner)
        response = api_client.get(_list_url(trip.id, day.id))
        assert response.status_code == 200
        assert [a["id"] for a in response.data] == [early.id, late.id]

    def test_day_must_belong_to_trip(self, api_client, auth, make_user, make_trip, trip_with_day):
        owner, trip, day = trip_with_day
        other_owner = make_user("c@test.com", "c")
        other_trip = make_trip(other_owner, title="別人的行程")
        other_day = TripDay.objects.create(trip=other_trip, date=date(2026, 7, 1))
        auth(owner)
        response = api_client.get(_list_url(trip.id, other_day.id))
        assert response.status_code == 404


@pytest.mark.django_db
class TestActivityUpdate:
    def test_reorder_activity(self, api_client, auth, trip_with_day):
        owner, trip, day = trip_with_day
        first = Activity.objects.create(day=day, title="淺草寺", order=1)
        second = Activity.objects.create(day=day, title="晚餐", order=2)
        auth(owner)
        response = api_client.patch(_detail_url(trip.id, day.id, second.id), {"order": 0})
        assert response.status_code == 200
        listing = api_client.get(_list_url(trip.id, day.id))
        assert [a["id"] for a in listing.data] == [second.id, first.id]

    def test_move_activity_to_another_day_same_trip(self, api_client, auth, trip_with_day):
        owner, trip, day = trip_with_day
        other_day = TripDay.objects.create(trip=trip, date=date(2026, 7, 2))
        activity = Activity.objects.create(day=day, title="淺草寺")
        auth(owner)
        response = api_client.patch(_detail_url(trip.id, day.id, activity.id), {"day": other_day.id})
        assert response.status_code == 200
        activity.refresh_from_db()
        assert activity.day == other_day

    def test_cannot_move_to_day_of_other_trip(self, api_client, auth, make_user, make_trip, trip_with_day):
        owner, trip, day = trip_with_day
        other_owner = make_user("c@test.com", "c")
        other_trip = make_trip(other_owner, title="別人的行程")
        foreign_day = TripDay.objects.create(trip=other_trip, date=date(2026, 7, 1))
        activity = Activity.objects.create(day=day, title="淺草寺")
        auth(owner)
        response = api_client.patch(_detail_url(trip.id, day.id, activity.id), {"day": foreign_day.id})
        assert response.status_code == 400
        assert "day" in response.data
        activity.refresh_from_db()
        assert activity.day == day


@pytest.mark.django_db
class TestActivityDelete:
    def test_editor_can_delete(self, api_client, make_user, auth, share_trip, trip_with_day):
        owner, trip, day = trip_with_day
        editor = make_user("b@test.com", "b")
        share_trip(trip, editor, TripMember.Role.EDITOR)
        activity = Activity.objects.create(day=day, title="淺草寺")
        auth(editor)
        response = api_client.delete(_detail_url(trip.id, day.id, activity.id))
        assert response.status_code == 204
        assert not Activity.objects.filter(id=activity.id).exists()
