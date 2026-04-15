import json
import uuid
from typing import TYPE_CHECKING

from src.exceptions import ConfirmationTokenNotFoundException

if TYPE_CHECKING:
    from src.connectors.redis_connector import RedisManager

CONFIRM_TOKEN_TTL = 3600  # 1 hour
CONFIRM_KEY_PREFIX = "confirm:"


class ConfirmationService:
    """Stores and validates one-time confirmation tokens in Redis."""

    def __init__(self, redis: "RedisManager") -> None:
        self._redis = redis

    async def create_token(self, type_: str, user_id: int, payload: dict) -> str:
        """Creates a UUID confirmation token and stores its payload in Redis."""
        token = uuid.uuid4().hex
        data = {"type": type_, "user_id": user_id, **payload}
        await self._redis.set(
            f"{CONFIRM_KEY_PREFIX}{token}",
            json.dumps(data),
            expire=CONFIRM_TOKEN_TTL,
        )
        return token

    async def consume_token(self, token: str) -> dict:
        """Reads the token payload from Redis and deletes it (one-time use)."""
        key = f"{CONFIRM_KEY_PREFIX}{token}"
        raw = await self._redis.get(key)
        if not raw:
            raise ConfirmationTokenNotFoundException()
        await self._redis.delete(key)
        if isinstance(raw, bytes):
            raw = raw.decode()
        return json.loads(raw)
