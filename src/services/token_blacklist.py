import logging
from datetime import datetime, timezone

from src.connectors.redis_connector import RedisManager

logger = logging.getLogger(__name__)

_BLACKLIST_PREFIX = "blacklist:"


class TokenBlacklistService:
    """Управление JWT blacklist через Redis. Graceful degradation при недоступности Redis."""

    def __init__(self, redis: RedisManager) -> None:
        self._redis = redis

    @property
    def _available(self) -> bool:
        return self._redis.redis is not None

    async def add(self, token: str, payload: dict) -> None:
        """Заносит токен в blacklist с TTL = оставшееся время жизни токена."""
        if not self._available:
            logger.warning("Redis недоступен — токен не занесён в blacklist")
            return
        exp = payload.get("exp", 0)
        ttl = max(1, int(exp - datetime.now(tz=timezone.utc).timestamp()))
        try:
            await self._redis.set(f"{_BLACKLIST_PREFIX}{token}", "1", expire=ttl)
        except Exception as e:
            logger.warning("Не удалось занести токен в blacklist Redis: %s", e)

    async def is_blacklisted(self, token: str) -> bool:
        """Проверяет наличие токена в blacklist. При ошибке — возвращает False (graceful)."""
        if not self._available:
            return False
        try:
            return await self._redis.exists(f"{_BLACKLIST_PREFIX}{token}")
        except Exception as e:
            logger.warning("Не удалось проверить blacklist токенов: %s", e)
            return False
