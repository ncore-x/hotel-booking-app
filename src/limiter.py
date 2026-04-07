from slowapi import Limiter
from slowapi.util import get_remote_address

from src.config import settings

# В тестах rate limiting отключён — все запросы идут с 127.0.0.1 и быстро выбивают лимит.
# В продакшне — Redis, чтобы лимиты работали корректно при нескольких воркерах.
_enabled = settings.MODE != "TEST"
_storage_uri = settings.REDIS_URL if _enabled else "memory://"
limiter = Limiter(key_func=get_remote_address, storage_uri=_storage_uri, enabled=_enabled)
