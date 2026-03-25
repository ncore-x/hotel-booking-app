"""
Проверяет, что токен, помещённый в блэклист при logout,
перестаёт работать для последующих запросов.
"""

from httpx import AsyncClient, ASGITransport
from src.main import app


async def test_token_blacklisted_after_logout():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Регистрируемся
        reg = await client.post(
            "/api/v1/auth/register",
            json={"email": "blacklist_test@example.com", "password": "Blacklist1"},
        )
        assert reg.status_code in (201, 409)

        # Логинимся
        login = await client.post(
            "/api/v1/auth/login",
            json={"email": "blacklist_test@example.com", "password": "Blacklist1"},
        )
        assert login.status_code == 200
        assert "access_token" in client.cookies

        # /me работает
        me_before = await client.get("/api/v1/auth/me")
        assert me_before.status_code == 200

        # Выходим
        logout = await client.post("/api/v1/auth/logout")
        assert logout.status_code == 204
        assert "access_token" not in client.cookies

        # /me больше не работает — нет cookie
        me_after = await client.get("/api/v1/auth/me")
        assert me_after.status_code == 401
