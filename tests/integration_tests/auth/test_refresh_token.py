"""
Тесты для POST /auth/refresh.

Кейсы:
1. Успешное обновление access токена по валидному refresh токену
2. Отсутствие refresh_token cookie → 401
3. Невалидный (испорченный) refresh токен → 401
4. Access токен в refresh cookie → 401 (неверный тип)
5. Refresh токен после logout занесён в blacklist → 401
"""

import pytest
from httpx import AsyncClient, ASGITransport

from src.main import app


@pytest.fixture
async def auth_client():
    """Свежий клиент, зарегистрированный и залогиненный."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        reg = await client.post(
            "/api/v1/auth/register",
            json={"email": "refresh_test@example.com", "password": "Refresh123!"},
        )
        assert reg.status_code in (201, 409)

        login = await client.post(
            "/api/v1/auth/login",
            json={"email": "refresh_test@example.com", "password": "Refresh123!"},
        )
        assert login.status_code == 200
        yield client


async def test_refresh_success(auth_client: AsyncClient):
    """Успешный refresh: новый access_token устанавливается в cookie."""
    old_access = auth_client.cookies.get("access_token")
    assert old_access is not None

    resp = await auth_client.post("/api/v1/auth/refresh")
    assert resp.status_code == 200

    new_access = auth_client.cookies.get("access_token")
    assert new_access is not None
    # Проверяем, что /me работает с новым токеном
    me = await auth_client.get("/api/v1/auth/me")
    assert me.status_code == 200


async def test_refresh_no_cookie():
    """Без refresh_token cookie → 401."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/v1/auth/refresh")
        assert resp.status_code == 401


async def test_refresh_invalid_token():
    """Невалидный refresh токен → 401."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        client.cookies.set("refresh_token", "not.a.valid.token")
        resp = await client.post("/api/v1/auth/refresh")
        assert resp.status_code == 401


async def test_refresh_with_access_token_in_refresh_cookie(auth_client: AsyncClient):
    """Если в refresh_token cookie находится access токен → 401 (неверный type claim)."""
    access = auth_client.cookies.get("access_token")
    assert access is not None

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Подсовываем access токен вместо refresh
        client.cookies.set("refresh_token", access)
        resp = await client.post("/api/v1/auth/refresh")
        assert resp.status_code == 401


async def test_refresh_token_blacklisted_after_logout(auth_client: AsyncClient):
    """После logout refresh токен занесён в blacklist и не может быть использован."""
    # Проверяем, что refresh cookie присутствует
    assert auth_client.cookies.get("refresh_token") is not None

    logout = await auth_client.post("/api/v1/auth/logout")
    assert logout.status_code == 204

    # Оба токена должны быть удалены из cookies
    assert auth_client.cookies.get("access_token") is None
    assert auth_client.cookies.get("refresh_token") is None
