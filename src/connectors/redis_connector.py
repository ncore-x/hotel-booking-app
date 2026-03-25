import logging

import redis.asyncio as redis


class RedisManager:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.redis: redis.Redis | None = None

    async def connect(self):
        logging.info(f"Подключение к Redis host={self.host}, port={self.port}")
        self.redis = redis.Redis(host=self.host, port=self.port)
        logging.info(f"Redis подключён: host={self.host}, port={self.port}")

    async def ping(self) -> bool:
        if not self.redis:
            return False
        try:
            return await self.redis.ping()
        except Exception:
            return False

    async def set(self, key: str, value: str, expire: int | None = None):
        if expire:
            await self.redis.set(key, value, ex=expire)
        else:
            await self.redis.set(key, value)

    async def get(self, key: str):
        return await self.redis.get(key)

    async def exists(self, key: str) -> bool:
        return bool(await self.redis.exists(key))

    async def delete(self, key: str):
        await self.redis.delete(key)

    async def close(self):
        if self.redis:
            await self.redis.aclose()
