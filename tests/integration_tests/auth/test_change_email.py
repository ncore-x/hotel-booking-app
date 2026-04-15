"""
Тесты для PATCH /auth/me/email.

Кейсы:
1. Успешная смена email
2. Неверный пароль → 401
3. Новый email совпадает с текущим → 409
4. Новый email уже занят другим пользователем → 409
5. Невалидный email → 422
6. Без авторизации → 401
"""

from unittest.mock import MagicMock, patch

import pytest
from httpx import AsyncClient, ASGITransport

from src.main import app
from src.services.confirmation import ConfirmationService


@pytest.fixture
async def email_test_client():
    """Клиент с зарегистрированным и залогиненным пользователем."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post(
            "/api/v1/auth/register",
            json={"email": "email_change@example.com", "password": "EmailChange1!"},
        )
        login = await client.post(
            "/api/v1/auth/login",
            json={"email": "email_change@example.com", "password": "EmailChange1!"},
        )
        assert login.status_code == 200
        yield client


async def test_change_email_success(email_test_client: AsyncClient):
    """PATCH sends a confirmation token to Redis; GET /confirm applies the change."""
    captured: list[str] = []
    original = ConfirmationService.create_token

    async def _capture(self, *args, **kwargs):
        token = await original(self, *args, **kwargs)
        captured.append(token)
        return token

    with patch.object(ConfirmationService, "create_token", _capture):
        with patch("src.tasks.tasks.send_confirmation_email_task") as mock_task:
            mock_task.delay = MagicMock()
            resp = await email_test_client.patch(
                "/api/v1/auth/me/email",
                json={
                    "new_email": "email_changed@example.com",
                    "current_password": "EmailChange1!",
                },
            )
    assert resp.status_code == 204
    assert len(captured) == 1

    confirm = await email_test_client.get(f"/api/v1/auth/confirm?token={captured[0]}")
    assert confirm.status_code == 200

    # /me returns the new email
    me = await email_test_client.get("/api/v1/auth/me")
    assert me.status_code == 200
    assert me.json()["email"] == "email_changed@example.com"


async def test_change_email_wrong_password(email_test_client: AsyncClient):
    resp = await email_test_client.patch(
        "/api/v1/auth/me/email",
        json={"new_email": "other@example.com", "current_password": "WrongPass999!"},
    )
    assert resp.status_code == 401


async def test_change_email_same_email(email_test_client: AsyncClient):
    resp = await email_test_client.patch(
        "/api/v1/auth/me/email",
        json={"new_email": "email_change@example.com", "current_password": "EmailChange1!"},
    )
    assert resp.status_code == 409


async def test_change_email_already_taken():
    """Email занят другим пользователем → 409."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Регистрируем двух пользователей
        await client.post(
            "/api/v1/auth/register",
            json={"email": "taken_target@example.com", "password": "Taken1234!"},
        )
        await client.post(
            "/api/v1/auth/register",
            json={"email": "taken_source@example.com", "password": "Source1234!"},
        )
        await client.post(
            "/api/v1/auth/login",
            json={"email": "taken_source@example.com", "password": "Source1234!"},
        )
        resp = await client.patch(
            "/api/v1/auth/me/email",
            json={"new_email": "taken_target@example.com", "current_password": "Source1234!"},
        )
        assert resp.status_code == 409


async def test_change_email_invalid_format(email_test_client: AsyncClient):
    resp = await email_test_client.patch(
        "/api/v1/auth/me/email",
        json={"new_email": "not-an-email", "current_password": "EmailChange1!"},
    )
    assert resp.status_code == 422


async def test_change_email_unauthenticated():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.patch(
            "/api/v1/auth/me/email",
            json={"new_email": "any@example.com", "current_password": "AnyPass1!"},
        )
        assert resp.status_code == 401
