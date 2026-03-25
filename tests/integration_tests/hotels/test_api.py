from datetime import date, timedelta

import pytest
from httpx import AsyncClient


def future(days: int) -> str:
    return (date.today() + timedelta(days=days)).isoformat()


_DATE_FROM = future(30)
_DATE_TO = future(45)


# ──── GET /hotels ─────────────────────────────────────────────────────────────

async def test_get_hotels(ac: AsyncClient):
    response = await ac.get(
        "/api/v1/hotels",
        params={"date_from": _DATE_FROM, "date_to": _DATE_TO},
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "per_page" in data
    assert "pages" in data
    assert "has_next" in data
    assert "has_prev" in data
    assert isinstance(data["items"], list)


async def test_get_hotels_pagination(ac: AsyncClient):
    r = await ac.get(
        "/api/v1/hotels",
        params={"date_from": _DATE_FROM, "date_to": _DATE_TO, "per_page": 1, "page": 1},
    )
    assert r.status_code == 200
    assert len(r.json()["items"]) <= 1


async def test_get_hotels_sort_by_title(ac: AsyncClient):
    response = await ac.get(
        "/api/v1/hotels",
        params={"date_from": _DATE_FROM, "date_to": _DATE_TO, "sort_by": "title", "order": "asc"},
    )
    assert response.status_code == 200
    items = response.json()["items"]
    titles = [h["title"] for h in items]
    assert titles == sorted(titles)


async def test_get_hotels_invalid_date_range(ac: AsyncClient):
    response = await ac.get(
        "/api/v1/hotels",
        params={"date_from": _DATE_TO, "date_to": _DATE_FROM},
    )
    assert response.status_code == 422


async def test_get_hotels_x_request_id_echoed(ac: AsyncClient):
    custom_id = "hotels-test-id"
    response = await ac.get(
        "/api/v1/hotels",
        params={"date_from": _DATE_FROM, "date_to": _DATE_TO},
        headers={"X-Request-ID": custom_id},
    )
    assert response.headers["x-request-id"] == custom_id


# ──── GET /hotels/{hotel_id} ─────────────────────────────────────────────────

async def test_get_hotel_by_id(ac: AsyncClient):
    response = await ac.get("/api/v1/hotels/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert "title" in data
    assert "location" in data


async def test_get_hotel_not_found(ac: AsyncClient):
    response = await ac.get("/api/v1/hotels/999999")
    assert response.status_code == 404


# ──── POST /hotels (только admin) ────────────────────────────────────────────

async def test_create_hotel_forbidden_for_regular_user(authenticated_ac: AsyncClient):
    response = await authenticated_ac.post(
        "/api/v1/hotels",
        json={"title": "Forbidden Hotel", "location": "Nowhere"},
    )
    assert response.status_code == 403


async def test_create_hotel(admin_ac: AsyncClient):
    response = await admin_ac.post(
        "/api/v1/hotels",
        json={"title": "Test Hotel Alpha", "location": "Москва, ул. Тверская, 1"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Hotel Alpha"
    assert "id" in data
    assert "Location" in response.headers


async def test_create_hotel_duplicate(admin_ac: AsyncClient):
    payload = {"title": "Duplicate Hotel X", "location": "Дубль, ул. Тест, 1"}
    await admin_ac.post("/api/v1/hotels", json=payload)
    response = await admin_ac.post("/api/v1/hotels", json=payload)
    assert response.status_code == 409


# ──── PUT /hotels/{hotel_id} ─────────────────────────────────────────────────

async def test_put_hotel(admin_ac: AsyncClient):
    create = await admin_ac.post(
        "/api/v1/hotels",
        json={"title": "Hotel For Put", "location": "Краснодар"},
    )
    hotel_id = create.json()["id"]

    response = await admin_ac.put(
        f"/api/v1/hotels/{hotel_id}",
        json={"title": "Hotel For Put Updated", "location": "Краснодар Новый"},
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Hotel For Put Updated"


async def test_put_hotel_not_found(admin_ac: AsyncClient):
    response = await admin_ac.put(
        "/api/v1/hotels/999999",
        json={"title": "Ghost Hotel", "location": "Nowhere"},
    )
    assert response.status_code == 404


# ──── PATCH /hotels/{hotel_id} ───────────────────────────────────────────────

async def test_patch_hotel(admin_ac: AsyncClient):
    create = await admin_ac.post(
        "/api/v1/hotels",
        json={"title": "Hotel For Patch", "location": "Сочи"},
    )
    hotel_id = create.json()["id"]

    response = await admin_ac.patch(
        f"/api/v1/hotels/{hotel_id}",
        json={"title": "Hotel For Patch Updated"},
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Hotel For Patch Updated"
    assert response.json()["location"] == "Сочи"


async def test_patch_hotel_not_found(admin_ac: AsyncClient):
    response = await admin_ac.patch("/api/v1/hotels/999999", json={"title": "Ghost"})
    assert response.status_code == 404


# ──── DELETE /hotels/{hotel_id} ──────────────────────────────────────────────

async def test_delete_hotel(admin_ac: AsyncClient):
    create = await admin_ac.post(
        "/api/v1/hotels",
        json={"title": "Hotel To Delete", "location": "Удалённый город"},
    )
    hotel_id = create.json()["id"]

    assert (await admin_ac.delete(f"/api/v1/hotels/{hotel_id}")).status_code == 204
    assert (await admin_ac.get(f"/api/v1/hotels/{hotel_id}")).status_code == 404


async def test_delete_hotel_not_found(admin_ac: AsyncClient):
    response = await admin_ac.delete("/api/v1/hotels/999999")
    assert response.status_code == 404


async def test_delete_hotel_with_rooms_returns_409(admin_ac: AsyncClient):
    """Нельзя удалить отель, у которого есть номера."""
    # hotel_id=1 содержит номера из mock_rooms.json
    response = await admin_ac.delete("/api/v1/hotels/1")
    assert response.status_code == 409
