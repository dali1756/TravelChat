from datetime import date

import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError

from trips.models import Activity, Attraction, Trip, TripDay, TripMember

User = get_user_model()


def _make_user(email, username):
    return User.objects.create_user(email=email, username=username, password="Aa1!xy", is_active=True)


def _make_trip(owner, **kwargs):
    defaults = {
        "title": "東京五日遊",
        "start_date": date(2026, 7, 1),
        "end_date": date(2026, 7, 5),
    }
    defaults.update(kwargs)
    return Trip.objects.create(owner=owner, **defaults)


@pytest.mark.django_db
class TestTripModel:
    def test_create_trip_with_owner(self):
        user = _make_user("a@test.com", "a")
        trip = _make_trip(user)
        assert trip.owner == user
        assert trip.title == "東京五日遊"
        assert trip.start_date == date(2026, 7, 1)
        assert trip.end_date == date(2026, 7, 5)
        assert trip.description == ""

    def test_for_user_includes_owned_and_shared_trips(self):
        owner = _make_user("a@test.com", "a")
        member = _make_user("b@test.com", "b")
        outsider = _make_user("c@test.com", "c")
        owned = _make_trip(owner)
        shared = _make_trip(member, title="大阪行")
        TripMember.objects.create(trip=owned, user=member, role=TripMember.Role.VIEWER)

        assert set(Trip.objects.for_user(owner)) == {owned}
        assert set(Trip.objects.for_user(member)) == {owned, shared}
        assert set(Trip.objects.for_user(outsider)) == set()


@pytest.mark.django_db
class TestTripDayModel:
    def test_unique_date_per_trip(self):
        user = _make_user("a@test.com", "a")
        trip = _make_trip(user)
        TripDay.objects.create(trip=trip, date=date(2026, 7, 1))
        with pytest.raises(IntegrityError):
            TripDay.objects.create(trip=trip, date=date(2026, 7, 1))

    def test_days_ordered_by_date(self):
        user = _make_user("a@test.com", "a")
        trip = _make_trip(user)
        day2 = TripDay.objects.create(trip=trip, date=date(2026, 7, 2))
        day1 = TripDay.objects.create(trip=trip, date=date(2026, 7, 1))
        assert list(trip.days.all()) == [day1, day2]


@pytest.mark.django_db
class TestTripMemberModel:
    def test_unique_user_per_trip(self):
        owner = _make_user("a@test.com", "a")
        member = _make_user("b@test.com", "b")
        trip = _make_trip(owner)
        TripMember.objects.create(trip=trip, user=member)
        with pytest.raises(IntegrityError):
            TripMember.objects.create(trip=trip, user=member)

    def test_role_defaults_to_viewer(self):
        owner = _make_user("a@test.com", "a")
        member = _make_user("b@test.com", "b")
        trip = _make_trip(owner)
        record = TripMember.objects.create(trip=trip, user=member)
        assert record.role == TripMember.Role.VIEWER


@pytest.mark.django_db
class TestActivityModel:
    def test_activities_ordered_by_order_then_id(self):
        user = _make_user("a@test.com", "a")
        trip = _make_trip(user)
        day = TripDay.objects.create(trip=trip, date=date(2026, 7, 1))
        second = Activity.objects.create(day=day, title="晚餐", order=2)
        first = Activity.objects.create(day=day, title="淺草寺", order=1)
        same_order = Activity.objects.create(day=day, title="飯店休息", order=2)
        assert list(day.activities.all()) == [first, second, same_order]

    def test_activity_without_attraction(self):
        user = _make_user("a@test.com", "a")
        trip = _make_trip(user)
        day = TripDay.objects.create(trip=trip, date=date(2026, 7, 1))
        activity = Activity.objects.create(day=day, title="機場集合")
        assert activity.attraction is None
        assert activity.order == 0


@pytest.mark.django_db
class TestAttractionModel:
    def test_attraction_survives_creator_hard_deletion(self):
        user = _make_user("a@test.com", "a")
        attraction = Attraction.objects.create(name="淺草寺", created_by=user)
        # User.delete() 是 soft delete，這裡用 queryset 硬刪除驗證 DB 層的 SET_NULL
        User.objects.filter(pk=user.pk).delete()
        attraction.refresh_from_db()
        assert attraction.created_by is None
        assert attraction.name == "淺草寺"
