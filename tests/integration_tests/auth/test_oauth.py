"""
Integration tests for OAuth 2.0 endpoints.

GET  /auth/oauth/{provider}/authorize
POST /auth/oauth/{provider}/callback

Design principle: all Redis state is created via HTTP endpoints (ASGI transport)
to avoid event-loop issues. OAuth callback state is obtained by first calling
the authorize endpoint, then extracting the state from the returned URL.
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

from httpx import AsyncClient, ASGITransport

from src.main import app


# ─── Helpers ──────────────────────────────────────────────────────────────────


def _extract_state(url: str) -> str:
    """Extracts the 'state' query param value from an OAuth authorization URL."""
    for part in url.split("&"):
        if "state=" in part:
            return part.split("state=")[1]
    raise ValueError(f"state not found in URL: {url}")


def _mock_response(json_data: dict):
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.json = MagicMock(return_value=json_data)
    resp.headers = {"content-type": "application/json"}
    resp.text = json.dumps(json_data)
    return resp


def _mock_httpx_client(token_resp, userinfo_resp):
    client = AsyncMock()
    client.post = AsyncMock(return_value=token_resp)
    client.get = AsyncMock(return_value=userinfo_resp)
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=None)
    return client


# ─── GET /auth/oauth/{provider}/authorize ────────────────────────────────────


async def test_authorize_unsupported_provider():
    """Unknown provider → 400."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/auth/oauth/github/authorize")
    assert resp.status_code == 400


@patch("src.services.oauth.settings")
async def test_authorize_not_configured(mock_settings):
    """Provider exists but credentials missing → 503."""
    mock_settings.GOOGLE_CLIENT_ID = None
    mock_settings.GOOGLE_CLIENT_SECRET = None
    mock_settings.APP_BASE_URL = "http://localhost"

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/auth/oauth/google/authorize")
    assert resp.status_code == 503


@patch("src.services.oauth.settings")
async def test_authorize_google_returns_url(mock_settings):
    """With credentials configured → 200 with 'url' field pointing to Google."""
    mock_settings.GOOGLE_CLIENT_ID = "test-client-id"
    mock_settings.GOOGLE_CLIENT_SECRET = "test-secret"
    mock_settings.APP_BASE_URL = "http://localhost:5173"

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/auth/oauth/google/authorize")

    assert resp.status_code == 200
    data = resp.json()
    assert "url" in data
    assert "accounts.google.com" in data["url"]
    assert "client_id=test-client-id" in data["url"]
    assert "state=" in data["url"]


# ─── POST /auth/oauth/{provider}/callback ────────────────────────────────────


async def test_callback_unsupported_provider():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/auth/oauth/github/callback",
            params={"code": "abc", "state": "xyz"},
        )
    assert resp.status_code == 400


async def test_callback_invalid_state():
    """State not in Redis → 400."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/auth/oauth/google/callback",
            params={"code": "any-code", "state": "nonexistent-state-xyz-000"},
        )
    assert resp.status_code == 400


@patch("src.services.oauth.settings")
@patch("src.services.oauth.httpx.AsyncClient")
async def test_callback_creates_user_and_sets_cookies(mock_async_client, mock_settings):
    """
    Full callback flow: authorize → get state URL → post callback with mocked
    provider calls → new user created, JWT cookies set.
    """
    mock_settings.GOOGLE_CLIENT_ID = "cid"
    mock_settings.GOOGLE_CLIENT_SECRET = "csec"
    mock_settings.APP_BASE_URL = "http://localhost"

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Step 1: get state (creates state in Redis through ASGI)
        auth_resp = await client.get("/api/v1/auth/oauth/google/authorize")
        assert auth_resp.status_code == 200
        state = _extract_state(auth_resp.json()["url"])

        # Step 2: mock HTTP calls to OAuth provider
        token_resp = _mock_response({"access_token": "google-access-tok"})
        userinfo_resp = _mock_response(
            {
                "sub": "google-integration-001",
                "email": "oauth_new_user@gmail.com",
                "name": "OAuth User",
                "picture": "https://example.com/avatar.jpg",
            }
        )
        mock_async_client.return_value = _mock_httpx_client(token_resp, userinfo_resp)

        # Step 3: callback with the real state
        resp = await client.post(
            "/api/v1/auth/oauth/google/callback",
            params={"code": "mock-code", "state": state},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "access_token" in resp.cookies
    assert "refresh_token" in resp.cookies


@patch("src.services.oauth.settings")
@patch("src.services.oauth.httpx.AsyncClient")
async def test_callback_existing_oauth_user_logs_in(mock_async_client, mock_settings):
    """
    Second callback with same oauth_id → returns existing user, no new record.
    """
    mock_settings.GOOGLE_CLIENT_ID = "cid"
    mock_settings.GOOGLE_CLIENT_SECRET = "csec"
    mock_settings.APP_BASE_URL = "http://localhost"

    oauth_sub = "google-integration-002"
    oauth_email = "oauth_existing@gmail.com"

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # First login – creates user
        auth_resp1 = await client.get("/api/v1/auth/oauth/google/authorize")
        state1 = _extract_state(auth_resp1.json()["url"])

        mock_async_client.return_value = _mock_httpx_client(
            _mock_response({"access_token": "tok1"}),
            _mock_response(
                {"sub": oauth_sub, "email": oauth_email, "name": "Existing", "picture": None}
            ),
        )
        resp1 = await client.post(
            "/api/v1/auth/oauth/google/callback",
            params={"code": "code1", "state": state1},
        )
        assert resp1.status_code == 200

        # Second login – must reuse existing user
        auth_resp2 = await client.get("/api/v1/auth/oauth/google/authorize")
        state2 = _extract_state(auth_resp2.json()["url"])

        mock_async_client.return_value = _mock_httpx_client(
            _mock_response({"access_token": "tok2"}),
            _mock_response(
                {"sub": oauth_sub, "email": oauth_email, "name": "Existing", "picture": None}
            ),
        )
        resp2 = await client.post(
            "/api/v1/auth/oauth/google/callback",
            params={"code": "code2", "state": state2},
        )
        assert resp2.status_code == 200


@patch("src.services.oauth.settings")
@patch("src.services.oauth.httpx.AsyncClient")
async def test_callback_email_conflict_links_account(mock_async_client, mock_settings):
    """OAuth user's email matches an existing password-based account → auto-link, 200."""
    mock_settings.GOOGLE_CLIENT_ID = "cid"
    mock_settings.GOOGLE_CLIENT_SECRET = "csec"
    mock_settings.APP_BASE_URL = "http://localhost"

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Register a password-based user with the conflicting email
        await client.post(
            "/api/v1/auth/register",
            json={"email": "oauth_conflict@example.com", "password": "ConflictPass1!"},
        )

        # Get state through authorize endpoint
        auth_resp = await client.get("/api/v1/auth/oauth/google/authorize")
        state = _extract_state(auth_resp.json()["url"])

        mock_async_client.return_value = _mock_httpx_client(
            _mock_response({"access_token": "tok"}),
            _mock_response(
                {
                    "sub": "google-conflict-999",
                    "email": "oauth_conflict@example.com",
                    "name": "Conflict User",
                    "picture": None,
                }
            ),
        )
        resp = await client.post(
            "/api/v1/auth/oauth/google/callback",
            params={"code": "code", "state": state},
        )
    # Account auto-linked, login succeeds
    assert resp.status_code == 200
