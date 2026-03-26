from slowapi import Limiter
from slowapi.util import get_remote_address

from src.config import settings

# Ключ — IP клиента. Redis storage гарантирует корректный подсчёт при нескольких воркерах.
limiter = Limiter(key_func=get_remote_address, storage_uri=settings.REDIS_URL)
