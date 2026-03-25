from datetime import date, timedelta

import pytest
from httpx import AsyncClient


def future(days: int) -> str:
    return (date.today() + timedelta(days=days)).isoformat()


_DATE_FROM = future(30)
_DATE_TO = future(45)


# ──── GET /hotels/{hotel_id}/rooms ────────────────────────────────────────────


async def test_get_rooms(ac: AsyncClient):
    response = await ac.get(
        "/api/v1/hotels/1/rooms",
        params={"date_from": _DATE_FROM, "date_to": _DATE_TO},
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert isinstance(data["items"], list)


async def test_get_rooms_hotel_not_found(ac: AsyncClient):
    response = await ac.get(
        "/api/v1/hotels/999999/rooms",
        params={"date_from": _DATE_FROM, "date_to": _DATE_TO},
    )
    assert response.status_code == 404


async def test_get_rooms_invalid_date_range(ac: AsyncClient):
    response = await ac.get(
        "/api/v1/hotels/1/rooms",
        params={"date_from": _DATE_TO, "date_to": _DATE_FROM},
    )
    assert response.status_code == 422


# ──── GET /hotels/{hotel_id}/rooms/{room_id} ─────────────────────────────────


async def test_get_room_by_id(ac: AsyncClient):
    response = await ac.get("/api/v1/hotels/1/rooms/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["hotel_id"] == 1


async def test_get_room_not_found(ac: AsyncClient):
    response = await ac.get("/api/v1/hotels/1/rooms/999999")
    assert response.status_code == 404


async def test_get_room_wrong_hotel(ac: AsyncClient):
    response = await ac.get("/api/v1/hotels/2/rooms/1")
    assert response.status_code in (404, 422)


# ──── POST /hotels/{hotel_id}/rooms (только admin) ────────────────────────────


async def test_create_room_forbidden_for_regular_user(authenticated_ac: AsyncClient):
    response = await authenticated_ac.post(
        "/api/v1/hotels/1/rooms",
        json={
            "title": "Forbidden Room",
            "description": None,
            "price": 1000,
            "quantity": 1,
            "facilities_ids": [],
        },
    )
    assert response.status_code == 403


@pytest.fixture(scope="module")
async def created_room(admin_ac: AsyncClient):
    response = await admin_ac.post(
        "/api/v1/hotels/1/rooms",
        json={
            "title": "Test Room Suite",
            "description": "Тест",
            "price": 9999,
            "quantity": 3,
            "facilities_ids": [],
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


async def test_create_room(admin_ac: AsyncClient, created_room):
    assert created_room["title"] == "Test Room Suite"
    assert created_room["price"] == 9999
    assert "id" in created_room
    assert created_room["hotel_id"] == 1


async def test_create_room_has_location_header(admin_ac: AsyncClient):
    response = await admin_ac.post(
        "/api/v1/hotels/1/rooms",
        json={
            "title": "Room With Location",
            "description": None,
            "price": 5000,
            "quantity": 1,
            "facilities_ids": [],
        },
    )
    assert response.status_code == 201
    assert "Location" in response.headers


async def test_create_room_hotel_not_found(admin_ac: AsyncClient):
    response = await admin_ac.post(
        "/api/v1/hotels/999999/rooms",
        json={
            "title": "Ghost Room",
            "description": None,
            "price": 1000,
            "quantity": 1,
            "facilities_ids": [],
        },
    )
    assert response.status_code == 404


# ──── PUT /hotels/{hotel_id}/rooms/{room_id} ─────────────────────────────────


async def test_put_room(admin_ac: AsyncClient, created_room):
    room_id = created_room["id"]
    response = await admin_ac.put(
        f"/api/v1/hotels/1/rooms/{room_id}",
        json={
            "title": "Suite Updated",
            "description": "Обновлён",
            "price": 12000,
            "quantity": 2,
            "facilities_ids": [],
        },
    )
    assert response.status_code == 200
    assert response.json()["price"] == 12000


async def test_put_room_not_found(admin_ac: AsyncClient):
    response = await admin_ac.put(
        "/api/v1/hotels/1/rooms/999999",
        json={
            "title": "Ghost",
            "description": None,
            "price": 1000,
            "quantity": 1,
            "facilities_ids": [],
        },
    )
    assert response.status_code == 404


# ──── PATCH /hotels/{hotel_id}/rooms/{room_id} ───────────────────────────────


async def test_patch_room(admin_ac: AsyncClient, created_room):
    room_id = created_room["id"]
    response = await admin_ac.patch(
        f"/api/v1/hotels/1/rooms/{room_id}",
        json={"price": 7777},
    )
    assert response.status_code == 200
    assert response.json()["price"] == 7777


async def test_patch_room_not_found(admin_ac: AsyncClient):
    response = await admin_ac.patch("/api/v1/hotels/1/rooms/999999", json={"price": 100})
    assert response.status_code == 404


# ──── DELETE /hotels/{hotel_id}/rooms/{room_id} ──────────────────────────────


async def test_delete_room(admin_ac: AsyncClient):
    create = await admin_ac.post(
        "/api/v1/hotels/2/rooms",
        json={
            "title": "Room To Delete",
            "description": None,
            "price": 2000,
            "quantity": 1,
            "facilities_ids": [],
        },
    )
    assert create.status_code == 201
    room_id = create.json()["id"]

    assert (await admin_ac.delete(f"/api/v1/hotels/2/rooms/{room_id}")).status_code == 204
    assert (await admin_ac.get(f"/api/v1/hotels/2/rooms/{room_id}")).status_code == 404


async def test_delete_room_not_found(admin_ac: AsyncClient):
    response = await admin_ac.delete("/api/v1/hotels/1/rooms/999999")
    assert response.status_code == 404
