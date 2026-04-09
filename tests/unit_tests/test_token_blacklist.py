"""Unit tests for TokenBlacklistService."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from src.services.token_blacklist import TokenBlacklistService


@pytest.fixture
def redis_mock():
    mock = AsyncMock()
    mock.redis = AsyncMock()
    return mock


@pytest.fixture
def service(redis_mock):
    return TokenBlacklistService(redis=redis_mock)


@pytest.fixture
def service_no_redis():
    mock = AsyncMock()
    mock.redis = None
    return TokenBlacklistService(redis=mock)


async def test_add_token(service: TokenBlacklistService, redis_mock):
    exp = datetime.now(tz=timezone.utc).timestamp() + 3600
    await service.add("test-token", {"exp": exp})
    redis_mock.set.assert_called_once()
    call_args = redis_mock.set.call_args
    assert call_args[0][0] == "blacklist:test-token"
    assert call_args[0][1] == "1"
    assert call_args[1]["expire"] > 0


async def test_add_token_redis_unavailable(service_no_redis: TokenBlacklistService):
    await service_no_redis.add("test-token", {"exp": 0})
    # Should not raise


async def test_add_token_redis_exception(service: TokenBlacklistService, redis_mock):
    redis_mock.set.side_effect = ConnectionError("fail")
    exp = datetime.now(tz=timezone.utc).timestamp() + 3600
    await service.add("test-token", {"exp": exp})
    # Should not raise, graceful degradation


async def test_is_blacklisted_true(service: TokenBlacklistService, redis_mock):
    redis_mock.exists.return_value = True
    result = await service.is_blacklisted("test-token")
    assert result is True
    redis_mock.exists.assert_called_once_with("blacklist:test-token")


async def test_is_blacklisted_false(service: TokenBlacklistService, redis_mock):
    redis_mock.exists.return_value = False
    result = await service.is_blacklisted("test-token")
    assert result is False


async def test_is_blacklisted_redis_unavailable(service_no_redis: TokenBlacklistService):
    result = await service_no_redis.is_blacklisted("test-token")
    assert result is False


async def test_is_blacklisted_redis_exception(service: TokenBlacklistService, redis_mock):
    redis_mock.exists.side_effect = ConnectionError("fail")
    result = await service.is_blacklisted("test-token")
    assert result is False
