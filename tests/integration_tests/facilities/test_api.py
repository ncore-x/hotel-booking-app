from httpx import AsyncClient


async def test_get_facilities(ac: AsyncClient):
    response = await ac.get("/api/v1/facilities")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "pages" in data
    assert isinstance(data["items"], list)


async def test_get_facilities_has_next_prev(ac: AsyncClient):
    response = await ac.get("/api/v1/facilities", params={"per_page": 1, "page": 1})
    assert response.status_code == 200
    data = response.json()
    assert "has_next" in data
    assert "has_prev" in data
    assert data["has_prev"] is False


async def test_post_facilities_forbidden_for_regular_user(authenticated_ac: AsyncClient):
    response = await authenticated_ac.post("/api/v1/facilities", json={"title": "Forbidden"})
    assert response.status_code == 403


async def test_post_facilities(admin_ac: AsyncClient):
    facility_title = "Массаж"
    response = await admin_ac.post("/api/v1/facilities", json={"title": facility_title})
    assert response.status_code == 201
    res = response.json()
    assert isinstance(res, dict)
    assert res["title"] == facility_title
    assert "id" in res
    assert "Location" in response.headers
