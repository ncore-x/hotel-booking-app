from unittest.mock import MagicMock, patch

import pytest
from httpx import AsyncClient

from src.services.confirmation import ConfirmationService


@pytest.mark.parametrize(
    "email, password, status_code",
    [
        ("k0t@pes.com", "Password123", 201),
        ("k0t@pes.com", "Password123", 409),
        ("k0t1@pes.com", "Password456", 201),
        ("abcde", "Password123", 422),
        ("abcde@abc", "Password123", 422),
    ],
)
async def test_auth_flow(email: str, password: str, status_code: int, ac: AsyncClient):
    resp_register = await ac.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )
    assert resp_register.status_code == status_code, (
        f"Expected {status_code}, got {resp_register.status_code}. Response: {resp_register.text}"
    )

    if status_code != 201:
        return

    user = resp_register.json()
    assert user["email"] == email.lower()
    assert "id" in user
    assert "password" not in user
    assert "hashed_password" not in user
    assert "Location" in resp_register.headers

    resp_login = await ac.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert resp_login.status_code == 200
    assert ac.cookies["access_token"]
    assert "access_token" in resp_login.json()
    assert resp_login.json()["token_type"] == "bearer"

    resp_me = await ac.get("/api/v1/auth/me")
    assert resp_me.status_code == 200
    me = resp_me.json()
    assert me["email"] == email.lower()
    assert "id" in me
    assert "password" not in me
    assert "hashed_password" not in me

    resp_logout = await ac.post("/api/v1/auth/logout")
    assert resp_logout.status_code == 204
    assert "access_token" not in ac.cookies


# ──── /me без токена ─────────────────────────────────────────────────────────


async def test_get_me_unauthenticated(unauth_ac: AsyncClient):
    response = await unauth_ac.get("/api/v1/auth/me")
    assert response.status_code == 401


# ──── /login — ошибочные данные ───────────────────────────────────────────────


async def test_login_wrong_password(ac: AsyncClient):
    # Пользователь зарегистрирован в conftest (test@example.com)
    response = await ac.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "WrongPass999"},
    )
    assert response.status_code == 401


async def test_login_unregistered_email(ac: AsyncClient):
    response = await ac.post(
        "/api/v1/auth/login",
        json={"email": "nobody@notexist.com", "password": "ValidPass1"},
    )
    assert response.status_code == 401


# ──── /register — невалидные данные ──────────────────────────────────────────


@pytest.mark.parametrize(
    "email, password",
    [
        ("", "ValidPass1"),  # пустой email
        ("notanemail", "ValidPass1"),  # email без @
        ("user@nodot", "ValidPass1"),  # email без точки в домене
        ("ok@test.com", "short"),  # пароль слишком короткий
        ("ok@test.com", "nouppercase1"),  # нет заглавной буквы
        ("ok@test.com", "NOLOWERCASE1"),  # нет строчной буквы
        ("ok@test.com", "NoDigitsHere"),  # нет цифры
    ],
)
async def test_register_invalid_data(email: str, password: str, ac: AsyncClient):
    response = await ac.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )
    assert response.status_code == 422


# ──── PATCH /auth/me — смена пароля ──────────────────────────────────────────


async def test_change_password(unauth_ac: AsyncClient):
    """Регистрируемся, меняем пароль через confirmation flow, логинимся с новым паролем."""
    captured: list[str] = []
    original = ConfirmationService.create_token

    async def _capture(self, *args, **kwargs):
        token = await original(self, *args, **kwargs)
        captured.append(token)
        return token

    reg = await unauth_ac.post(
        "/api/v1/auth/register",
        json={"email": "changepass@example.com", "password": "OldPass123"},
    )
    assert reg.status_code in (201, 409)

    login = await unauth_ac.post(
        "/api/v1/auth/login",
        json={"email": "changepass@example.com", "password": "OldPass123"},
    )
    assert login.status_code == 200

    with patch.object(ConfirmationService, "create_token", _capture):
        with patch("src.tasks.tasks.send_confirmation_email_task") as mock_task:
            mock_task.delay = MagicMock()
            patch_resp = await unauth_ac.patch(
                "/api/v1/auth/me",
                json={"current_password": "OldPass123", "new_password": "NewPass456"},
            )
    assert patch_resp.status_code == 204
    assert len(captured) == 1

    confirm_resp = await unauth_ac.get(f"/api/v1/auth/confirm?token={captured[0]}")
    assert confirm_resp.status_code == 200

    # Logout so subsequent login attempts are not blocked by the existing cookie
    await unauth_ac.post("/api/v1/auth/logout")

    # Old password no longer works
    bad_login = await unauth_ac.post(
        "/api/v1/auth/login",
        json={"email": "changepass@example.com", "password": "OldPass123"},
    )
    assert bad_login.status_code == 401

    # New password works
    new_login = await unauth_ac.post(
        "/api/v1/auth/login",
        json={"email": "changepass@example.com", "password": "NewPass456"},
    )
    assert new_login.status_code == 200


async def test_change_password_wrong_current(authenticated_ac: AsyncClient):
    response = await authenticated_ac.patch(
        "/api/v1/auth/me",
        json={"current_password": "WrongPass999", "new_password": "NewPass456"},
    )
    assert response.status_code == 401


async def test_change_password_unauthenticated(unauth_ac: AsyncClient):
    response = await unauth_ac.patch(
        "/api/v1/auth/me",
        json={"current_password": "OldPass123", "new_password": "NewPass456"},
    )
    assert response.status_code == 401


async def test_change_password_weak_new_password(authenticated_ac: AsyncClient):
    response = await authenticated_ac.patch(
        "/api/v1/auth/me",
        json={"current_password": "TestPassword123", "new_password": "weak"},
    )
    assert response.status_code == 422


async def test_me_has_password_true_for_password_user(unauth_ac: AsyncClient):
    """Пользователь с паролем получает has_password=true в /me."""
    await unauth_ac.post(
        "/api/v1/auth/register",
        json={"email": "haspass@example.com", "password": "HasPass123"},
    )
    await unauth_ac.post(
        "/api/v1/auth/login",
        json={"email": "haspass@example.com", "password": "HasPass123"},
    )
    resp = await unauth_ac.get("/api/v1/auth/me")
    assert resp.status_code == 200
    data = resp.json()
    assert data["has_password"] is True
    assert "hashed_password" not in data


async def test_me_has_password_false_for_oauth_user(unauth_ac: AsyncClient):
    """OAuth-пользователь (без пароля) получает has_password=false в /me."""
    from unittest.mock import patch, AsyncMock, MagicMock
    from httpx import AsyncClient as HttpxClient
    from httpx._transports.asgi import ASGITransport
    from src.main import app

    def _mock_resp(data):
        r = MagicMock()
        r.json = MagicMock(return_value=data)
        r.raise_for_status = MagicMock()
        r.headers = {"content-type": "application/json"}
        return r

    def _mock_client(token_resp, userinfo_resp):
        client = MagicMock()
        client.__aenter__ = AsyncMock(return_value=client)
        client.__aexit__ = AsyncMock(return_value=False)
        client.post = AsyncMock(return_value=token_resp)
        client.get = AsyncMock(return_value=userinfo_resp)
        return client

    with (
        patch("src.services.oauth.settings") as mock_cfg,
        patch("src.services.oauth.httpx.AsyncClient") as mock_http,
    ):
        mock_cfg.GOOGLE_CLIENT_ID = "cid"
        mock_cfg.GOOGLE_CLIENT_SECRET = "csec"
        mock_cfg.APP_BASE_URL = "http://localhost"

        transport = ASGITransport(app=app)
        async with HttpxClient(transport=transport, base_url="http://test") as ac:
            auth_resp = await ac.get("/api/v1/auth/oauth/google/authorize")
            from tests.integration_tests.auth.test_oauth import _extract_state

            state = _extract_state(auth_resp.json()["url"])

            mock_http.return_value = _mock_client(
                _mock_resp({"access_token": "tok"}),
                _mock_resp(
                    {
                        "sub": "google-nopass-001",
                        "email": "oauthonly@example.com",
                        "name": "OAuth User",
                        "picture": None,
                    }
                ),
            )
            cb = await ac.post(
                "/api/v1/auth/oauth/google/callback",
                params={"code": "code", "state": state},
            )
            assert cb.status_code == 200

            me = await ac.get("/api/v1/auth/me")
            assert me.status_code == 200
            assert me.json()["has_password"] is False
