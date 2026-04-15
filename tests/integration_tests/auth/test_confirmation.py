"""
Integration tests for confirmation flow.

Tests GET /auth/confirm?token= endpoint and the full PATCH→confirm cycle
for both password and email changes.

All Redis access goes through ASGI transport (HTTP endpoints) to avoid
event-loop mismatch issues between the session fixture loop and function loops.
Tokens are captured by patching ConfirmationService.create_token.
"""

from unittest.mock import MagicMock, patch

from httpx import AsyncClient, ASGITransport

from src.main import app
from src.services.confirmation import ConfirmationService


# ─── Helper ───────────────────────────────────────────────────────────────────


def _capture_token_patcher():
    """Returns (captured list, context manager) for intercepting create_token."""
    captured: list[str] = []
    original = ConfirmationService.create_token

    async def _wrapped(self, *args, **kwargs):
        token = await original(self, *args, **kwargs)
        captured.append(token)
        return token

    return captured, patch.object(ConfirmationService, "create_token", _wrapped)


# ─── GET /auth/confirm — basic endpoint behaviour ────────────────────────────


async def test_confirm_invalid_token():
    """Unknown token → 404."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/auth/confirm?token=nonexistenttoken000000000000000")
    assert resp.status_code == 400


# ─── Full PATCH → confirm cycle ───────────────────────────────────────────────


async def test_confirm_email_change():
    """
    Full cycle: PATCH /auth/me/email → token stored in Redis (through ASGI) →
    GET /auth/confirm → email changed.
    """
    captured, token_patch = _capture_token_patcher()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post(
            "/api/v1/auth/register",
            json={"email": "confirm_email@example.com", "password": "Confirm1234!"},
        )
        await client.post(
            "/api/v1/auth/login",
            json={"email": "confirm_email@example.com", "password": "Confirm1234!"},
        )

        with token_patch, patch("src.tasks.tasks.send_confirmation_email_task") as mt:
            mt.delay = MagicMock()
            resp = await client.patch(
                "/api/v1/auth/me/email",
                json={
                    "new_email": "confirmed_email@example.com",
                    "current_password": "Confirm1234!",
                },
            )
        assert resp.status_code == 204
        assert len(captured) == 1

        confirm = await client.get(f"/api/v1/auth/confirm?token={captured[0]}")
        assert confirm.status_code == 200

        me = await client.get("/api/v1/auth/me")
        assert me.json()["email"] == "confirmed_email@example.com"


async def test_confirm_password_change():
    """
    Full cycle: PATCH /auth/me → token stored in Redis (through ASGI) →
    GET /auth/confirm → new password works, old password doesn't.
    """
    captured, token_patch = _capture_token_patcher()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post(
            "/api/v1/auth/register",
            json={"email": "confirm_pass@example.com", "password": "OldPass1234!"},
        )
        await client.post(
            "/api/v1/auth/login",
            json={"email": "confirm_pass@example.com", "password": "OldPass1234!"},
        )

        with token_patch, patch("src.tasks.tasks.send_confirmation_email_task") as mt:
            mt.delay = MagicMock()
            resp = await client.patch(
                "/api/v1/auth/me",
                json={"current_password": "OldPass1234!", "new_password": "NewPass5678!"},
            )
        assert resp.status_code == 204
        assert len(captured) == 1

        confirm = await client.get(f"/api/v1/auth/confirm?token={captured[0]}")
        assert confirm.status_code == 200

        await client.post("/api/v1/auth/logout")

        bad = await client.post(
            "/api/v1/auth/login",
            json={"email": "confirm_pass@example.com", "password": "OldPass1234!"},
        )
        assert bad.status_code == 401

        good = await client.post(
            "/api/v1/auth/login",
            json={"email": "confirm_pass@example.com", "password": "NewPass5678!"},
        )
        assert good.status_code == 200


async def test_confirm_token_is_one_time_use():
    """After consuming a token once, a second call returns 404."""
    captured, token_patch = _capture_token_patcher()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post(
            "/api/v1/auth/register",
            json={"email": "onetime_confirm@example.com", "password": "OneTime1234!"},
        )
        await client.post(
            "/api/v1/auth/login",
            json={"email": "onetime_confirm@example.com", "password": "OneTime1234!"},
        )

        with token_patch, patch("src.tasks.tasks.send_confirmation_email_task") as mt:
            mt.delay = MagicMock()
            await client.patch(
                "/api/v1/auth/me/email",
                json={
                    "new_email": "onetime_done@example.com",
                    "current_password": "OneTime1234!",
                },
            )
        assert len(captured) == 1

        first = await client.get(f"/api/v1/auth/confirm?token={captured[0]}")
        assert first.status_code == 200

        second = await client.get(f"/api/v1/auth/confirm?token={captured[0]}")
        assert second.status_code == 400


async def test_patch_wrong_password_does_not_create_token():
    """PATCH with wrong password → 401, no token created."""
    captured, token_patch = _capture_token_patcher()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post(
            "/api/v1/auth/register",
            json={"email": "wrongpass_confirm@example.com", "password": "RightPass1!"},
        )
        await client.post(
            "/api/v1/auth/login",
            json={"email": "wrongpass_confirm@example.com", "password": "RightPass1!"},
        )

        with token_patch, patch("src.tasks.tasks.send_confirmation_email_task") as mt:
            mt.delay = MagicMock()
            resp = await client.patch(
                "/api/v1/auth/me",
                json={"current_password": "WrongPass999!", "new_password": "NewPass123!"},
            )
        assert resp.status_code == 401
        assert len(captured) == 0
