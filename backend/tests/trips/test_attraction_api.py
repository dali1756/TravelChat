import pytest

from trips.models import Attraction

URL = "/api/trips/attractions/"


@pytest.mark.django_db
class TestAttractionCreate:
    def test_create_attraction(self, api_client, make_user, auth):
        user = make_user("a@test.com", "a")
        auth(user)
        response = api_client.post(
            URL,
            {
                "name": "淺草寺",
                "address": "東京都台東區淺草2-3-1",
                "latitude": "35.714765",
                "longitude": "139.796655",
                "description": "東京最古老的寺院",
            },
        )
        assert response.status_code == 201
        attraction = Attraction.objects.get(id=response.data["id"])
        assert attraction.created_by == user
        assert attraction.name == "淺草寺"

    def test_name_is_required(self, api_client, make_user, auth):
        user = make_user("a@test.com", "a")
        auth(user)
        response = api_client.post(URL, {"address": "某處"})
        assert response.status_code == 400
        assert "name" in response.data

    def test_create_requires_auth(self, api_client):
        response = api_client.post(URL, {"name": "淺草寺"})
        assert response.status_code == 401


@pytest.mark.django_db
class TestAttractionList:
    def test_lists_attractions_from_all_users(self, api_client, make_user, auth):
        user = make_user("a@test.com", "a")
        other = make_user("b@test.com", "b")
        Attraction.objects.create(name="淺草寺", created_by=user)
        Attraction.objects.create(name="晴空塔", created_by=other)
        auth(user)
        response = api_client.get(URL)
        assert response.status_code == 200
        names = {a["name"] for a in response.data}
        assert names == {"淺草寺", "晴空塔"}

    def test_retrieve_single_attraction(self, api_client, make_user, auth):
        user = make_user("a@test.com", "a")
        attraction = Attraction.objects.create(name="淺草寺", created_by=user)
        auth(user)
        response = api_client.get(f"{URL}{attraction.id}/")
        assert response.status_code == 200
        assert response.data["name"] == "淺草寺"

    def test_list_requires_auth(self, api_client):
        response = api_client.get(URL)
        assert response.status_code == 401
