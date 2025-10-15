import pytest
from httpx import AsyncClient

from tests.conftest import get_db_null_pool
from src.utils.db_manager import DBManager


@pytest.mark.parametrize(
    "room_id, date_from, date_to, status_code",
    [
        (1, "2025-11-01", "2025-11-15", 200),
        (1, "2025-11-01", "2025-11-15", 200),
        (1, "2025-11-01", "2025-11-15", 200),
        (1, "2025-11-01", "2025-11-15", 200),
        (1, "2025-11-01", "2025-11-15", 200),
        (1, "2025-11-01", "2025-11-15", 409),
    ],
)
async def test_add_booking(
    room_id, date_from, date_to, status_code, db: DBManager, authenticated_ac: AsyncClient
):
    response = await authenticated_ac.post(
        "/bookings",
        json={
            "room_id": room_id,
            "date_from": date_from,
            "date_to": date_to,
        },
    )

    print("=== BOOKING DEBUG ===")
    print(f"Room ID: {room_id}, Date from: {date_from}, Date to: {date_to}")
    print(f"Expected status: {status_code}, Actual status: {response.status_code}")
    print(f"Response body: {response.text}")
    print("=====================")

    assert response.status_code == status_code, (
        f"Expected {status_code}, got {response.status_code}. Response: {response.text}"
    )

    if status_code == 200:
        res = response.json()
        assert isinstance(res, dict)
        assert "detail" in res
        assert "data" in res
        assert "Номер успешно забронирован!" in res["detail"]


@pytest.fixture(scope="module")
async def delete_all_bookings():
    async for _db in get_db_null_pool():
        await _db.bookings.delete()
        await _db.commit()


@pytest.mark.parametrize(
    "room_id, date_from, date_to, booked_rooms",
    [
        (1, "2025-11-01", "2025-11-10", 1),
        (1, "2025-11-02", "2025-11-11", 2),
        (1, "2025-11-03", "2025-11-12", 3),
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
        "/bookings",
        json={
            "room_id": room_id,
            "date_from": date_from,
            "date_to": date_to,
        },
    )

    print("=== MY BOOKINGS DEBUG ===")
    print(f"Room ID: {room_id}, Date from: {date_from}, Date to: {date_to}")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    print("========================")

    assert response.status_code == 200, f"Booking failed: {response.text}"

    response_my_bookings = await authenticated_ac.get("/bookings/me")
    assert response_my_bookings.status_code == 200

    my_bookings_data = response_my_bookings.json()
    print(f"My bookings response: {my_bookings_data}")

    if isinstance(my_bookings_data, list):
        assert len(my_bookings_data) == booked_rooms
    elif isinstance(my_bookings_data, dict) and "data" in my_bookings_data:
        assert len(my_bookings_data["data"]) == booked_rooms
    else:
        assert False, f"Unexpected response format: {my_bookings_data}"
