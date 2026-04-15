"""Unit tests for OAuthService."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.exceptions import (
    InvalidOAuthStateException,
    OAuthEmailConflictException,
    OAuthProviderNotConfiguredException,
    UnsupportedOAuthProviderException,
)
from src.services.oauth import OAuthService, OAUTH_STATE_PREFIX


# ─── Helpers ──────────────────────────────────────────────────────────────────


def _make_redis(state_value=None):
    redis = MagicMock()
    redis.set = AsyncMock()
    redis.get = AsyncMock(return_value=state_value)
    redis.delete = AsyncMock()
    return redis


def _make_db():
    db = MagicMock()
    db.users = AsyncMock()
    db.commit = AsyncMock()
    return db


def _make_service(db=None, redis=None):
    return OAuthService(db=db or _make_db(), redis=redis or _make_redis())


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


# ─── create_authorization_url ─────────────────────────────────────────────────


@patch("src.services.oauth.settings")
async def test_create_url_google_contains_required_params(mock_settings):
    mock_settings.GOOGLE_CLIENT_ID = "test-client-id"
    mock_settings.GOOGLE_CLIENT_SECRET = "test-secret"
    mock_settings.APP_BASE_URL = "http://localhost:5173"

    redis = _make_redis()
    svc = _make_service(redis=redis)

    url = await svc.create_authorization_url("google")

    assert "accounts.google.com" in url
    assert "client_id=test-client-id" in url
    assert "response_type=code" in url
    assert "scope=openid" in url
    assert "state=" in url


@patch("src.services.oauth.settings")
async def test_create_url_stores_state_in_redis(mock_settings):
    mock_settings.GOOGLE_CLIENT_ID = "cid"
    mock_settings.GOOGLE_CLIENT_SECRET = "csec"
    mock_settings.APP_BASE_URL = "http://localhost"

    redis = _make_redis()
    svc = _make_service(redis=redis)

    await svc.create_authorization_url("google")

    redis.set.assert_called_once()
    key = redis.set.call_args.args[0]
    assert key.startswith(OAUTH_STATE_PREFIX)
    value = redis.set.call_args.args[1]
    assert value == "google"


@patch("src.services.oauth.settings")
async def test_create_url_state_in_url_matches_redis_key(mock_settings):
    mock_settings.GOOGLE_CLIENT_ID = "cid"
    mock_settings.GOOGLE_CLIENT_SECRET = "csec"
    mock_settings.APP_BASE_URL = "http://localhost"

    redis = _make_redis()
    svc = _make_service(redis=redis)

    url = await svc.create_authorization_url("google")

    # Extract state from URL
    state_part = next(p for p in url.split("&") if p.startswith("state=") or "state=" in p)
    state_value = state_part.split("state=")[1]

    key = redis.set.call_args.args[0]
    assert key == f"{OAUTH_STATE_PREFIX}{state_value}"


async def test_create_url_unsupported_provider_raises():
    svc = _make_service()
    with pytest.raises(UnsupportedOAuthProviderException):
        await svc.create_authorization_url("github")


@patch("src.services.oauth.settings")
async def test_create_url_not_configured_raises(mock_settings):
    mock_settings.GOOGLE_CLIENT_ID = None
    mock_settings.GOOGLE_CLIENT_SECRET = None

    svc = _make_service()
    with pytest.raises(OAuthProviderNotConfiguredException):
        await svc.create_authorization_url("google")


@patch("src.services.oauth.settings")
async def test_create_url_missing_secret_raises(mock_settings):
    mock_settings.GOOGLE_CLIENT_ID = "cid"
    mock_settings.GOOGLE_CLIENT_SECRET = None

    svc = _make_service()
    with pytest.raises(OAuthProviderNotConfiguredException):
        await svc.create_authorization_url("google")


# ─── handle_callback ──────────────────────────────────────────────────────────


async def test_handle_callback_unsupported_provider():
    svc = _make_service()
    with pytest.raises(UnsupportedOAuthProviderException):
        await svc.handle_callback("twitter", "code", "state")


async def test_handle_callback_invalid_state_not_in_redis():
    redis = _make_redis(state_value=None)
    svc = _make_service(redis=redis)

    with pytest.raises(InvalidOAuthStateException):
        await svc.handle_callback("google", "code", "bad-state")


async def test_handle_callback_state_provider_mismatch():
    # Redis has "someotherprovider" but we're handling as "google"
    # → the stored value doesn't match provider → InvalidOAuthStateException
    redis = _make_redis(state_value=b"someotherprovider")
    svc = _make_service(redis=redis)

    with pytest.raises(InvalidOAuthStateException):
        await svc.handle_callback("google", "code", "state")


@patch("src.services.oauth.settings")
@patch("src.services.oauth.httpx.AsyncClient")
async def test_handle_callback_creates_new_user(mock_async_client, mock_settings):
    mock_settings.GOOGLE_CLIENT_ID = "cid"
    mock_settings.GOOGLE_CLIENT_SECRET = "csecret"
    mock_settings.APP_BASE_URL = "http://localhost"

    token_resp = _mock_response({"access_token": "tok123"})
    userinfo_resp = _mock_response(
        {
            "sub": "google-user-123",
            "email": "newuser@gmail.com",
            "name": "John Doe",
            "picture": "https://example.com/photo.jpg",
        }
    )
    mock_async_client.return_value = _mock_httpx_client(token_resp, userinfo_resp)

    redis = _make_redis(state_value=b"google")
    db = _make_db()
    db.users.get_by_oauth = AsyncMock(return_value=None)
    db.users.get_one_or_none = AsyncMock(return_value=None)
    new_user = MagicMock(id=99)
    db.users.create_oauth_user = AsyncMock(return_value=new_user)

    svc = _make_service(db=db, redis=redis)
    user, is_new = await svc.handle_callback("google", "auth-code", "valid-state")

    assert is_new is True
    assert user is new_user
    db.users.create_oauth_user.assert_called_once()
    db.commit.assert_called_once()


@patch("src.services.oauth.settings")
@patch("src.services.oauth.httpx.AsyncClient")
async def test_handle_callback_returns_existing_user(mock_async_client, mock_settings):
    mock_settings.GOOGLE_CLIENT_ID = "cid"
    mock_settings.GOOGLE_CLIENT_SECRET = "csecret"
    mock_settings.APP_BASE_URL = "http://localhost"

    token_resp = _mock_response({"access_token": "tok"})
    userinfo_resp = _mock_response(
        {
            "sub": "google-user-456",
            "email": "existing@gmail.com",
            "name": "Jane",
            "picture": None,
        }
    )
    mock_async_client.return_value = _mock_httpx_client(token_resp, userinfo_resp)

    redis = _make_redis(state_value="google")
    db = _make_db()
    existing_user = MagicMock(id=10)
    db.users.get_by_oauth = AsyncMock(return_value=existing_user)

    svc = _make_service(db=db, redis=redis)
    user, is_new = await svc.handle_callback("google", "code", "state")

    assert is_new is False
    assert user is existing_user
    db.users.create_oauth_user.assert_not_called()
    db.commit.assert_not_called()


@patch("src.services.oauth.settings")
@patch("src.services.oauth.httpx.AsyncClient")
async def test_handle_callback_email_conflict_raises(mock_async_client, mock_settings):
    mock_settings.GOOGLE_CLIENT_ID = "cid"
    mock_settings.GOOGLE_CLIENT_SECRET = "csecret"
    mock_settings.APP_BASE_URL = "http://localhost"

    token_resp = _mock_response({"access_token": "tok"})
    userinfo_resp = _mock_response(
        {
            "sub": "google-xyz",
            "email": "conflict@example.com",
            "name": "User",
            "picture": None,
        }
    )
    mock_async_client.return_value = _mock_httpx_client(token_resp, userinfo_resp)

    redis = _make_redis(state_value="google")
    db = _make_db()
    db.users.get_by_oauth = AsyncMock(return_value=None)
    # Existing password-based user with same email
    existing = MagicMock(oauth_provider=None)
    db.users.get_one_or_none = AsyncMock(return_value=existing)

    svc = _make_service(db=db, redis=redis)
    with pytest.raises(OAuthEmailConflictException):
        await svc.handle_callback("google", "code", "state")


@patch("src.services.oauth.settings")
@patch("src.services.oauth.httpx.AsyncClient")
async def test_handle_callback_state_deleted_after_use(mock_async_client, mock_settings):
    """State key must be deleted from Redis after successful verification."""
    mock_settings.GOOGLE_CLIENT_ID = "cid"
    mock_settings.GOOGLE_CLIENT_SECRET = "csecret"
    mock_settings.APP_BASE_URL = "http://localhost"

    token_resp = _mock_response({"access_token": "tok"})
    userinfo_resp = _mock_response(
        {
            "sub": "google-999",
            "email": "fresh@gmail.com",
            "name": "New",
            "picture": None,
        }
    )
    mock_async_client.return_value = _mock_httpx_client(token_resp, userinfo_resp)

    redis = _make_redis(state_value="google")
    db = _make_db()
    db.users.get_by_oauth = AsyncMock(return_value=None)
    db.users.get_one_or_none = AsyncMock(return_value=None)
    db.users.create_oauth_user = AsyncMock(return_value=MagicMock(id=1))

    svc = _make_service(db=db, redis=redis)
    await svc.handle_callback("google", "code", "mystate")

    redis.delete.assert_called_once_with(f"{OAUTH_STATE_PREFIX}mystate")


@patch("src.services.oauth.settings")
@patch("src.services.oauth.httpx.AsyncClient")
async def test_handle_callback_no_oauth_id_raises(mock_async_client, mock_settings):
    """If userinfo returns no 'sub', OAuthProviderNotConfiguredException is raised."""
    mock_settings.GOOGLE_CLIENT_ID = "cid"
    mock_settings.GOOGLE_CLIENT_SECRET = "csecret"
    mock_settings.APP_BASE_URL = "http://localhost"

    token_resp = _mock_response({"access_token": "tok"})
    userinfo_resp = _mock_response({"email": "x@x.com", "name": "X"})  # no sub / id
    mock_async_client.return_value = _mock_httpx_client(token_resp, userinfo_resp)

    redis = _make_redis(state_value="google")
    svc = _make_service(redis=redis)

    with pytest.raises(OAuthProviderNotConfiguredException):
        await svc.handle_callback("google", "code", "state")
