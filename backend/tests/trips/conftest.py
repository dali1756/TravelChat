from datetime import date

import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def make_user(db):
    def _make(email, username):
        return User.objects.create_user(email=email, username=username, password="Aa1!xy", is_active=True)

    return _make


@pytest.fixture
def auth(api_client):
    def _auth(user):
        response = api_client.post("/api/auth/login/", {"email": user.email, "password": "Aa1!xy"})
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")

    return _auth


@pytest.fixture
def make_trip(db):
    def _make(owner, **kwargs):
        from trips.models import Trip

        defaults = {
            "title": "東京五日遊",
            "start_date": date(2026, 7, 1),
            "end_date": date(2026, 7, 5),
        }
        defaults.update(kwargs)
        return Trip.objects.create(owner=owner, **defaults)

    return _make


@pytest.fixture
def share_trip(db):
    def _share(trip, user, role):
        from trips.models import TripMember

        return TripMember.objects.create(trip=trip, user=user, role=role)

    return _share
