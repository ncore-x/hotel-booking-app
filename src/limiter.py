from slowapi import Limiter
from slowapi.util import get_remote_address

from src.config import settings

# В тестах используем memory-хранилище, чтобы не зависеть от Redis.
# В продакшне — Redis, чтобы лимиты работали корректно при нескольких воркерах.
_storage_uri = "memory://" if settings.MODE == "TEST" else settings.REDIS_URL
limiter = Limiter(key_func=get_remote_address, storage_uri=_storage_uri)
