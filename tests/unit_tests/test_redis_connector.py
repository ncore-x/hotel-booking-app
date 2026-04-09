"""Unit tests for RedisManager connector."""

from unittest.mock import AsyncMock, patch

import pytest

from src.connectors.redis_connector import RedisManager


@pytest.fixture
def manager():
    return RedisManager(host="localhost", port=6379)


async def test_connect(manager: RedisManager):
    with patch("src.connectors.redis_connector.redis.Redis") as mock_redis:
        await manager.connect()
        mock_redis.assert_called_once_with(host="localhost", port=6379)
        assert manager.redis is not None


async def test_ping_no_connection(manager: RedisManager):
    assert await manager.ping() is False


async def test_ping_success(manager: RedisManager):
    manager.redis = AsyncMock()
    manager.redis.ping.return_value = True
    assert await manager.ping() is True


async def test_ping_exception(manager: RedisManager):
    manager.redis = AsyncMock()
    manager.redis.ping.side_effect = ConnectionError("fail")
    assert await manager.ping() is False


async def test_set_with_expire(manager: RedisManager):
    manager.redis = AsyncMock()
    await manager.set("key", "value", expire=60)
    manager.redis.set.assert_called_once_with("key", "value", ex=60)


async def test_set_without_expire(manager: RedisManager):
    manager.redis = AsyncMock()
    await manager.set("key", "value")
    manager.redis.set.assert_called_once_with("key", "value")


async def test_get(manager: RedisManager):
    manager.redis = AsyncMock()
    manager.redis.get.return_value = b"value"
    result = await manager.get("key")
    assert result == b"value"


async def test_exists(manager: RedisManager):
    manager.redis = AsyncMock()
    manager.redis.exists.return_value = 1
    assert await manager.exists("key") is True


async def test_delete(manager: RedisManager):
    manager.redis = AsyncMock()
    await manager.delete("key")
    manager.redis.delete.assert_called_once_with("key")


async def test_close(manager: RedisManager):
    manager.redis = AsyncMock()
    await manager.close()
    manager.redis.aclose.assert_called_once()


async def test_close_no_connection(manager: RedisManager):
    await manager.close()  # should not raise
