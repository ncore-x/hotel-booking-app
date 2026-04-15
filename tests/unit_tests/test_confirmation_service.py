"""Unit tests for ConfirmationService."""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.exceptions import ConfirmationTokenNotFoundException
from src.services.confirmation import (
    ConfirmationService,
    CONFIRM_KEY_PREFIX,
    CONFIRM_TOKEN_TTL,
)


# ─── Helpers ──────────────────────────────────────────────────────────────────


def _make_redis(get_value=None):
    redis = MagicMock()
    redis.set = AsyncMock()
    redis.get = AsyncMock(return_value=get_value)
    redis.delete = AsyncMock()
    return redis


def _make_service(redis=None):
    return ConfirmationService(redis=redis or _make_redis())


# ─── create_token ─────────────────────────────────────────────────────────────


async def test_create_token_returns_hex_string():
    svc = _make_service()
    token = await svc.create_token("password", user_id=1, payload={"new_hash": "h"})
    assert isinstance(token, str)
    assert len(token) == 32  # uuid4().hex


async def test_create_token_stores_correct_key():
    redis = _make_redis()
    svc = _make_service(redis)

    token = await svc.create_token("email", user_id=42, payload={"new_email": "a@b.com"})

    redis.set.assert_called_once()
    key = redis.set.call_args.args[0]
    assert key == f"{CONFIRM_KEY_PREFIX}{token}"


async def test_create_token_stores_correct_json():
    redis = _make_redis()
    svc = _make_service(redis)

    await svc.create_token("password", user_id=7, payload={"new_hash": "abc123"})

    value = redis.set.call_args.args[1]
    data = json.loads(value)
    assert data == {"type": "password", "user_id": 7, "new_hash": "abc123"}


async def test_create_token_uses_correct_ttl():
    redis = _make_redis()
    svc = _make_service(redis)

    await svc.create_token("email", user_id=1, payload={"new_email": "x@y.com"})

    kwargs = redis.set.call_args.kwargs
    assert kwargs.get("expire") == CONFIRM_TOKEN_TTL


async def test_create_token_merges_payload_fields():
    redis = _make_redis()
    svc = _make_service(redis)

    await svc.create_token("email", user_id=5, payload={"new_email": "x@y.com", "extra": "val"})

    value = redis.set.call_args.args[1]
    data = json.loads(value)
    assert data["type"] == "email"
    assert data["user_id"] == 5
    assert data["new_email"] == "x@y.com"
    assert data["extra"] == "val"


async def test_create_token_tokens_are_unique():
    redis = _make_redis()
    svc = _make_service(redis)

    token1 = await svc.create_token("password", 1, {"new_hash": "x"})
    token2 = await svc.create_token("password", 1, {"new_hash": "x"})

    assert token1 != token2


# ─── consume_token ────────────────────────────────────────────────────────────


async def test_consume_token_returns_payload_str():
    data = {"type": "email", "user_id": 7, "new_email": "new@example.com"}
    redis = _make_redis(get_value=json.dumps(data))
    svc = _make_service(redis)

    result = await svc.consume_token("sometoken")

    assert result == data


async def test_consume_token_returns_payload_bytes():
    data = {"type": "password", "user_id": 5, "new_hash": "hashed"}
    redis = _make_redis(get_value=json.dumps(data).encode())
    svc = _make_service(redis)

    result = await svc.consume_token("sometoken")

    assert result == data


async def test_consume_token_deletes_key():
    data = {"type": "password", "user_id": 3, "new_hash": "h"}
    redis = _make_redis(get_value=json.dumps(data))
    svc = _make_service(redis)

    await svc.consume_token("mytoken")

    redis.delete.assert_called_once_with(f"{CONFIRM_KEY_PREFIX}mytoken")


async def test_consume_token_not_found_raises():
    redis = _make_redis(get_value=None)
    svc = _make_service(redis)

    with pytest.raises(ConfirmationTokenNotFoundException):
        await svc.consume_token("nonexistent")


async def test_consume_token_not_found_does_not_delete():
    redis = _make_redis(get_value=None)
    svc = _make_service(redis)

    with pytest.raises(ConfirmationTokenNotFoundException):
        await svc.consume_token("nonexistent")

    redis.delete.assert_not_called()


async def test_consume_token_one_time_use():
    """Second consume of the same token must raise ConfirmationTokenNotFoundException."""
    call_count = 0

    async def _get(key):  # noqa: ARG001
        nonlocal call_count
        call_count += 1
        return (
            json.dumps({"type": "password", "user_id": 1, "new_hash": "h"})
            if call_count == 1
            else None
        )

    redis = _make_redis()
    redis.get = _get
    svc = _make_service(redis)

    await svc.consume_token("tok")  # first call succeeds

    with pytest.raises(ConfirmationTokenNotFoundException):
        await svc.consume_token("tok")  # second call raises
