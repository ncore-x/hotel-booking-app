from datetime import date, timedelta

import pytest
from httpx import AsyncClient

from tests.conftest import get_db_null_pool
from src.utils.db_manager import DBManager

# Даты всегда в будущем относительно момента запуска тестов
_D1_FROM = (date.today() + timedelta(days=60)).isoformat()
_D1_TO = (date.today() + timedelta(days=74)).isoformat()

_D2_FROM = (date.today() + timedelta(days=30)).isoformat()
_D2_TO = (date.today() + timedelta(days=39)).isoformat()
_D2B_FROM = (date.today() + timedelta(days=31)).isoformat()
_D2B_TO = (date.today() + timedelta(days=40)).isoformat()
_D2C_FROM = (date.today() + timedelta(days=32)).isoformat()
_D2C_TO = (date.today() + timedelta(days=41)).isoformat()


@pytest.mark.parametrize(
    "room_id, date_from, date_to, status_code",
    [
        (1, _D1_FROM, _D1_TO, 201),
        (1, _D1_FROM, _D1_TO, 201),
        (1, _D1_FROM, _D1_TO, 201),
        (1, _D1_FROM, _D1_TO, 201),
        (1, _D1_FROM, _D1_TO, 201),
        (1, _D1_FROM, _D1_TO, 409),
    ],
)
async def test_add_booking(
    room_id, date_from, date_to, status_code, db: DBManager, authenticated_ac: AsyncClient
):
    response = await authenticated_ac.post(
        "/api/v1/bookings",
        json={"room_id": room_id, "date_from": date_from, "date_to": date_to},
    )
    assert response.status_code == status_code, (
        f"Expected {status_code}, got {response.status_code}. Response: {response.text}"
    )

    if status_code == 201:
        res = response.json()
        assert isinstance(res, dict)
        assert "id" in res
        assert "room_id" in res
        assert "date_from" in res
        assert "Location" in response.headers


@pytest.fixture(scope="module")
async def delete_all_bookings():
    async for _db in get_db_null_pool():
        await _db.bookings.delete()
        await _db.commit()


@pytest.mark.parametrize(
    "room_id, date_from, date_to, booked_rooms",
    [
        (1, _D2_FROM, _D2_TO, 1),
        (1, _D2B_FROM, _D2B_TO, 2),
        (1, _D2C_FROM, _D2C_TO, 3),
    ],
)
async def test_add_and_get_my_bookings(
    room_id,
    date_from,
    date_to,
    booked_rooms,
    delete_all_bookings,
    authenticated_ac: AsyncClient,
):
    response = await authenticated_ac.post(
        "/api/v1/bookings",
        json={"room_id": room_id, "date_from": date_from, "date_to": date_to},
    )
    assert response.status_code == 201, f"Booking failed: {response.text}"

    response_my_bookings = await authenticated_ac.get("/api/v1/bookings/me")
    assert response_my_bookings.status_code == 200

    my_bookings_data = response_my_bookings.json()
    assert "items" in my_bookings_data, f"Expected paginated response, got: {my_bookings_data}"
    assert len(my_bookings_data["items"]) == booked_rooms


# ──── POST /bookings — ошибки валидации ──────────────────────────────────────

async def test_add_booking_past_date(authenticated_ac: AsyncClient):
    response = await authenticated_ac.post(
        "/api/v1/bookings",
        json={"room_id": 1, "date_from": "2020-01-01", "date_to": "2020-01-10"},
    )
    assert response.status_code == 422


async def test_add_booking_date_from_after_date_to(authenticated_ac: AsyncClient):
    from datetime import date, timedelta
    d_from = (date.today() + timedelta(days=10)).isoformat()
    d_to = (date.today() + timedelta(days=5)).isoformat()
    response = await authenticated_ac.post(
        "/api/v1/bookings",
        json={"room_id": 1, "date_from": d_from, "date_to": d_to},
    )
    assert response.status_code == 422


async def test_add_booking_room_not_found(authenticated_ac: AsyncClient):
    from datetime import date, timedelta
    response = await authenticated_ac.post(
        "/api/v1/bookings",
        json={
            "room_id": 999999,
            "date_from": (date.today() + timedelta(days=5)).isoformat(),
            "date_to": (date.today() + timedelta(days=10)).isoformat(),
        },
    )
    assert response.status_code == 404


# ──── GET /bookings/me — без аутентификации ───────────────────────────────────

async def test_get_my_bookings_unauthenticated(unauth_ac: AsyncClient):
    response = await unauth_ac.get("/api/v1/bookings/me")
    assert response.status_code == 401


# ──── DELETE /bookings/{booking_id} ──────────────────────────────────────────

async def test_cancel_booking(authenticated_ac: AsyncClient):
    from datetime import date, timedelta
    d_from = (date.today() + timedelta(days=80)).isoformat()
    d_to = (date.today() + timedelta(days=85)).isoformat()

    create_response = await authenticated_ac.post(
        "/api/v1/bookings",
        json={"room_id": 1, "date_from": d_from, "date_to": d_to},
    )
    assert create_response.status_code == 201
    booking_id = create_response.json()["id"]

    delete_response = await authenticated_ac.delete(f"/api/v1/bookings/{booking_id}")
    assert delete_response.status_code == 204


async def test_cancel_booking_not_found(authenticated_ac: AsyncClient):
    response = await authenticated_ac.delete("/api/v1/bookings/999999")
    assert response.status_code == 404


async def test_cancel_booking_unauthenticated(unauth_ac: AsyncClient):
    response = await unauth_ac.delete("/api/v1/bookings/1")
    assert response.status_code == 401


# ──── GET /bookings/me — pagination ──────────────────────────────────────────

async def test_get_my_bookings_paginated(authenticated_ac: AsyncClient):
    response = await authenticated_ac.get(
        "/api/v1/bookings/me", params={"page": 1, "per_page": 1}
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
    assert data["per_page"] == 1
    assert len(data["items"]) <= 1


# ──── GET /bookings/{id} ──────────────────────────────────────────────────────

async def test_get_booking_by_id(authenticated_ac: AsyncClient):
    from datetime import date, timedelta
    d_from = (date.today() + timedelta(days=100)).isoformat()
    d_to = (date.today() + timedelta(days=105)).isoformat()

    create = await authenticated_ac.post(
        "/api/v1/bookings",
        json={"room_id": 1, "date_from": d_from, "date_to": d_to},
    )
    assert create.status_code == 201
    booking_id = create.json()["id"]

    response = await authenticated_ac.get(f"/api/v1/bookings/{booking_id}")
    assert response.status_code == 200
    assert response.json()["id"] == booking_id


async def test_get_booking_not_found(authenticated_ac: AsyncClient):
    response = await authenticated_ac.get("/api/v1/bookings/999999")
    assert response.status_code == 404


async def test_get_booking_of_another_user(authenticated_ac: AsyncClient, admin_ac: AsyncClient):
    from datetime import date, timedelta
    d_from = (date.today() + timedelta(days=110)).isoformat()
    d_to = (date.today() + timedelta(days=115)).isoformat()

    create = await admin_ac.post(
        "/api/v1/bookings",
        json={"room_id": 1, "date_from": d_from, "date_to": d_to},
    )
    assert create.status_code == 201
    booking_id = create.json()["id"]

    # Regular user cannot see admin's booking
    response = await authenticated_ac.get(f"/api/v1/bookings/{booking_id}")
    assert response.status_code == 404


# ──── PATCH /bookings/{id} ────────────────────────────────────────────────────

async def test_patch_booking_dates(authenticated_ac: AsyncClient):
    from datetime import date, timedelta
    d_from = (date.today() + timedelta(days=120)).isoformat()
    d_to = (date.today() + timedelta(days=125)).isoformat()

    create = await authenticated_ac.post(
        "/api/v1/bookings",
        json={"room_id": 1, "date_from": d_from, "date_to": d_to},
    )
    assert create.status_code == 201
    booking_id = create.json()["id"]

    new_d_to = (date.today() + timedelta(days=128)).isoformat()
    patch = await authenticated_ac.patch(
        f"/api/v1/bookings/{booking_id}",
        json={"date_to": new_d_to},
    )
    assert patch.status_code == 200
    assert patch.json()["date_to"] == new_d_to


async def test_patch_booking_invalid_dates(authenticated_ac: AsyncClient):
    from datetime import date, timedelta
    d_from = (date.today() + timedelta(days=130)).isoformat()
    d_to = (date.today() + timedelta(days=135)).isoformat()

    create = await authenticated_ac.post(
        "/api/v1/bookings",
        json={"room_id": 1, "date_from": d_from, "date_to": d_to},
    )
    assert create.status_code == 201
    booking_id = create.json()["id"]

    # date_to earlier than date_from → 422
    bad_d_to = (date.today() + timedelta(days=129)).isoformat()
    patch = await authenticated_ac.patch(
        f"/api/v1/bookings/{booking_id}",
        json={"date_from": d_to, "date_to": bad_d_to},
    )
    assert patch.status_code == 422


async def test_patch_booking_not_found(authenticated_ac: AsyncClient):
    from datetime import date, timedelta
    response = await authenticated_ac.patch(
        "/api/v1/bookings/999999",
        json={"date_to": (date.today() + timedelta(days=5)).isoformat()},
    )
    assert response.status_code == 404
