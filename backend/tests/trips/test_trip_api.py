from datetime import date

import pytest

from trips.models import Activity, Trip, TripDay, TripMember

URL = "/api/trips/"


def _detail_url(trip_id):
    return f"/api/trips/{trip_id}/"


@pytest.mark.django_db
class TestTripCreate:
    def test_create_trip(self, api_client, make_user, auth):
        user = make_user("a@test.com", "a")
        auth(user)
        response = api_client.post(
            URL,
            {
                "title": "東京五日遊",
                "description": "夏季家族旅行",
                "start_date": "2026-07-01",
                "end_date": "2026-07-05",
            },
        )
        assert response.status_code == 201
        trip = Trip.objects.get(id=response.data["id"])
        assert trip.owner == user
        assert trip.title == "東京五日遊"

    def test_end_date_before_start_date(self, api_client, make_user, auth):
        user = make_user("a@test.com", "a")
        auth(user)
        response = api_client.post(
            URL,
            {"title": "壞行程", "start_date": "2026-07-05", "end_date": "2026-07-01"},
        )
        assert response.status_code == 400
        assert "end_date" in response.data

    def test_create_requires_auth(self, api_client):
        response = api_client.post(URL, {"title": "x", "start_date": "2026-07-01", "end_date": "2026-07-02"})
        assert response.status_code == 401


@pytest.mark.django_db
class TestTripList:
    def test_lists_only_participating_trips_with_role(self, api_client, make_user, auth, make_trip, share_trip):
        user = make_user("a@test.com", "a")
        owner_b = make_user("b@test.com", "b")
        owner_c = make_user("c@test.com", "c")
        owned = make_trip(user, title="我的行程")
        shared = make_trip(owner_b, title="朋友的行程")
        make_trip(owner_c, title="無關的行程")
        share_trip(shared, user, TripMember.Role.EDITOR)

        auth(user)
        response = api_client.get(URL)
        assert response.status_code == 200
        roles = {item["title"]: item["role"] for item in response.data}
        assert roles == {"我的行程": "owner", "朋友的行程": "editor"}
        ids = {item["id"] for item in response.data}
        assert ids == {owned.id, shared.id}

    def test_list_requires_auth(self, api_client):
        response = api_client.get(URL)
        assert response.status_code == 401


@pytest.mark.django_db
class TestTripDetail:
    def test_detail_includes_nested_days_and_activities(self, api_client, make_user, auth, make_trip):
        user = make_user("a@test.com", "a")
        trip = make_trip(user)
        day2 = TripDay.objects.create(trip=trip, date=date(2026, 7, 2))
        day1 = TripDay.objects.create(trip=trip, date=date(2026, 7, 1), note="抵達日")
        Activity.objects.create(day=day1, title="晚餐", order=2)
        Activity.objects.create(day=day1, title="淺草寺", order=1)

        auth(user)
        response = api_client.get(_detail_url(trip.id))
        assert response.status_code == 200
        days = response.data["days"]
        assert [d["id"] for d in days] == [day1.id, day2.id]
        assert [a["title"] for a in days[0]["activities"]] == ["淺草寺", "晚餐"]

    def test_viewer_can_read_detail(self, api_client, make_user, auth, make_trip, share_trip):
        owner = make_user("a@test.com", "a")
        viewer = make_user("b@test.com", "b")
        trip = make_trip(owner)
        share_trip(trip, viewer, TripMember.Role.VIEWER)
        auth(viewer)
        response = api_client.get(_detail_url(trip.id))
        assert response.status_code == 200

    def test_non_participant_gets_404(self, api_client, make_user, auth, make_trip):
        owner = make_user("a@test.com", "a")
        outsider = make_user("b@test.com", "b")
        trip = make_trip(owner)
        auth(outsider)
        assert api_client.get(_detail_url(trip.id)).status_code == 404
        assert api_client.patch(_detail_url(trip.id), {"title": "x"}).status_code == 404
        assert api_client.delete(_detail_url(trip.id)).status_code == 404


@pytest.mark.django_db
class TestTripUpdate:
    def test_owner_can_update(self, api_client, make_user, auth, make_trip):
        owner = make_user("a@test.com", "a")
        trip = make_trip(owner)
        auth(owner)
        response = api_client.patch(_detail_url(trip.id), {"title": "京都行"})
        assert response.status_code == 200
        trip.refresh_from_db()
        assert trip.title == "京都行"

    def test_editor_can_update(self, api_client, make_user, auth, make_trip, share_trip):
        owner = make_user("a@test.com", "a")
        editor = make_user("b@test.com", "b")
        trip = make_trip(owner)
        share_trip(trip, editor, TripMember.Role.EDITOR)
        auth(editor)
        response = api_client.patch(_detail_url(trip.id), {"title": "共編後的標題"})
        assert response.status_code == 200

    def test_viewer_cannot_update(self, api_client, make_user, auth, make_trip, share_trip):
        owner = make_user("a@test.com", "a")
        viewer = make_user("b@test.com", "b")
        trip = make_trip(owner)
        share_trip(trip, viewer, TripMember.Role.VIEWER)
        auth(viewer)
        response = api_client.patch(_detail_url(trip.id), {"title": "不該成功"})
        assert response.status_code == 403

    def test_shrink_date_range_with_existing_day_outside(self, api_client, make_user, auth, make_trip):
        owner = make_user("a@test.com", "a")
        trip = make_trip(owner)
        TripDay.objects.create(trip=trip, date=date(2026, 7, 5))
        auth(owner)
        response = api_client.patch(_detail_url(trip.id), {"end_date": "2026-07-03"})
        assert response.status_code == 400
        trip.refresh_from_db()
        assert trip.end_date == date(2026, 7, 5)


@pytest.mark.django_db
class TestTripDelete:
    def test_owner_can_delete(self, api_client, make_user, auth, make_trip):
        owner = make_user("a@test.com", "a")
        trip = make_trip(owner)
        auth(owner)
        response = api_client.delete(_detail_url(trip.id))
        assert response.status_code == 204
        assert not Trip.objects.filter(id=trip.id).exists()

    def test_editor_cannot_delete(self, api_client, make_user, auth, make_trip, share_trip):
        owner = make_user("a@test.com", "a")
        editor = make_user("b@test.com", "b")
        trip = make_trip(owner)
        share_trip(trip, editor, TripMember.Role.EDITOR)
        auth(editor)
        response = api_client.delete(_detail_url(trip.id))
        assert response.status_code == 403
        assert Trip.objects.filter(id=trip.id).exists()
