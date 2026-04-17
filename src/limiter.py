import logging

from slowapi import Limiter
from slowapi.util import get_remote_address

from src.config import settings

# В тестах rate limiting отключён — все запросы идут с 127.0.0.1 и быстро выбивают лимит.
# В продакшне — Redis, чтобы лимиты работали корректно при нескольких воркерах.
# Если Redis недоступен — падаем на memory://, чтобы не ломать эндпоинты.
_enabled = settings.MODE != "TEST"

if _enabled:
    try:
        import redis as _redis

        _r = _redis.from_url(settings.REDIS_URL, socket_connect_timeout=2)
        _r.ping()
        _r.close()
        _storage_uri = settings.REDIS_URL
        logging.info("Limiter: Redis storage (%s)", settings.REDIS_URL)
    except Exception as _e:
        _storage_uri = "memory://"
        logging.warning("Limiter: Redis недоступен (%s), используется memory://", _e)
else:
    _storage_uri = "memory://"

limiter = Limiter(key_func=get_remote_address, storage_uri=_storage_uri, enabled=_enabled)
