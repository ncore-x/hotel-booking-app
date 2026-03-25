"""
Тесты RBAC: is_admin в профиле, 401 vs 403, права администратора.
"""
from httpx import AsyncClient


async def test_regular_user_is_not_admin(authenticated_ac: AsyncClient):
    """Обычный пользователь имеет is_admin=false."""
    response = await authenticated_ac.get("/api/v1/auth/me")
    assert response.status_code == 200
    assert response.json()["is_admin"] is False


async def test_admin_user_is_admin(admin_ac: AsyncClient):
    """Администратор имеет is_admin=true."""
    response = await admin_ac.get("/api/v1/auth/me")
    assert response.status_code == 200
    assert response.json()["is_admin"] is True


async def test_unauthenticated_hotel_write_returns_401(unauth_ac: AsyncClient):
    """Без cookie — 401, не 403."""
    response = await unauth_ac.post(
        "/api/v1/hotels",
        json={"title": "Anon Hotel", "location": "Nowhere"},
    )
    assert response.status_code == 401


async def test_unauthenticated_room_write_returns_401(unauth_ac: AsyncClient):
    response = await unauth_ac.post(
        "/api/v1/hotels/1/rooms",
        json={"title": "Anon Room", "description": None, "price": 1000, "quantity": 1, "facilities_ids": []},
    )
    assert response.status_code == 401


async def test_unauthenticated_facility_write_returns_401(unauth_ac: AsyncClient):
    response = await unauth_ac.post("/api/v1/facilities", json={"title": "Anon Facility"})
    assert response.status_code == 401


async def test_regular_user_cannot_delete_hotel(authenticated_ac: AsyncClient):
    response = await authenticated_ac.delete("/api/v1/hotels/1")
    assert response.status_code == 403


async def test_regular_user_cannot_delete_room(authenticated_ac: AsyncClient):
    response = await authenticated_ac.delete("/api/v1/hotels/1/rooms/1")
    assert response.status_code == 403
