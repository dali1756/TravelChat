from datetime import date

import pytest

from trips.models import Activity, TripDay, TripMember


def _list_url(trip_id):
    return f"/api/trips/{trip_id}/days/"


def _detail_url(trip_id, day_id):
    return f"/api/trips/{trip_id}/days/{day_id}/"


@pytest.mark.django_db
class TestDayCreate:
    def test_owner_can_add_day(self, api_client, make_user, auth, make_trip):
        owner = make_user("a@test.com", "a")
        trip = make_trip(owner)
        auth(owner)
        response = api_client.post(_list_url(trip.id), {"date": "2026-07-02", "note": "市區觀光"})
        assert response.status_code == 201
        day = TripDay.objects.get(id=response.data["id"])
        assert day.trip == trip
        assert day.date == date(2026, 7, 2)

    def test_editor_can_add_day(self, api_client, make_user, auth, make_trip, share_trip):
        owner = make_user("a@test.com", "a")
        editor = make_user("b@test.com", "b")
        trip = make_trip(owner)
        share_trip(trip, editor, TripMember.Role.EDITOR)
        auth(editor)
        response = api_client.post(_list_url(trip.id), {"date": "2026-07-02"})
        assert response.status_code == 201

    def test_date_outside_trip_range(self, api_client, make_user, auth, make_trip):
        owner = make_user("a@test.com", "a")
        trip = make_trip(owner)
        auth(owner)
        response = api_client.post(_list_url(trip.id), {"date": "2026-07-09"})
        assert response.status_code == 400
        assert "date" in response.data

    def test_duplicate_date_in_same_trip(self, api_client, make_user, auth, make_trip):
        owner = make_user("a@test.com", "a")
        trip = make_trip(owner)
        TripDay.objects.create(trip=trip, date=date(2026, 7, 2))
        auth(owner)
        response = api_client.post(_list_url(trip.id), {"date": "2026-07-02"})
        assert response.status_code == 400
        assert "date" in response.data

    def test_viewer_cannot_add_day(self, api_client, make_user, auth, make_trip, share_trip):
        owner = make_user("a@test.com", "a")
        viewer = make_user("b@test.com", "b")
        trip = make_trip(owner)
        share_trip(trip, viewer, TripMember.Role.VIEWER)
        auth(viewer)
        response = api_client.post(_list_url(trip.id), {"date": "2026-07-02"})
        assert response.status_code == 403

    def test_non_participant_gets_404(self, api_client, make_user, auth, make_trip):
        owner = make_user("a@test.com", "a")
        outsider = make_user("b@test.com", "b")
        trip = make_trip(owner)
        auth(outsider)
        assert api_client.get(_list_url(trip.id)).status_code == 404
        assert api_client.post(_list_url(trip.id), {"date": "2026-07-02"}).status_code == 404


@pytest.mark.django_db
class TestDayList:
    def test_days_ordered_by_date(self, api_client, make_user, auth, make_trip):
        owner = make_user("a@test.com", "a")
        trip = make_trip(owner)
        day3 = TripDay.objects.create(trip=trip, date=date(2026, 7, 3))
        day1 = TripDay.objects.create(trip=trip, date=date(2026, 7, 1))
        auth(owner)
        response = api_client.get(_list_url(trip.id))
        assert response.status_code == 200
        assert [d["id"] for d in response.data] == [day1.id, day3.id]


@pytest.mark.django_db
class TestDayUpdate:
    def test_editor_can_update_note(self, api_client, make_user, auth, make_trip, share_trip):
        owner = make_user("a@test.com", "a")
        editor = make_user("b@test.com", "b")
        trip = make_trip(owner)
        day = TripDay.objects.create(trip=trip, date=date(2026, 7, 2))
        share_trip(trip, editor, TripMember.Role.EDITOR)
        auth(editor)
        response = api_client.patch(_detail_url(trip.id, day.id), {"note": "改去海邊"})
        assert response.status_code == 200
        day.refresh_from_db()
        assert day.note == "改去海邊"

    def test_viewer_cannot_update(self, api_client, make_user, auth, make_trip, share_trip):
        owner = make_user("a@test.com", "a")
        viewer = make_user("b@test.com", "b")
        trip = make_trip(owner)
        day = TripDay.objects.create(trip=trip, date=date(2026, 7, 2))
        share_trip(trip, viewer, TripMember.Role.VIEWER)
        auth(viewer)
        response = api_client.patch(_detail_url(trip.id, day.id), {"note": "不該成功"})
        assert response.status_code == 403


@pytest.mark.django_db
class TestDayDelete:
    def test_delete_day_cascades_activities(self, api_client, make_user, auth, make_trip):
        owner = make_user("a@test.com", "a")
        trip = make_trip(owner)
        day = TripDay.objects.create(trip=trip, date=date(2026, 7, 2))
        activity = Activity.objects.create(day=day, title="淺草寺")
        auth(owner)
        response = api_client.delete(_detail_url(trip.id, day.id))
        assert response.status_code == 204
        assert not TripDay.objects.filter(id=day.id).exists()
        assert not Activity.objects.filter(id=activity.id).exists()
