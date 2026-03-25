import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text

from src.database import engine_null_pool as _engine

router = APIRouter(prefix="/health", tags=["System"])


@router.get("", summary="Health check", include_in_schema=False)
async def health():
    """
    Проверяет доступность базы данных и Redis.
    Используется load balancer'ом и системами мониторинга.
    """
    db_ok = False
    redis_ok = False

    try:
        async with _engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        db_ok = True
    except Exception as e:
        logging.warning(f"Health: DB недоступна: {e}")

    try:
        from src.init import redis_manager

        redis_ok = await redis_manager.ping()
    except Exception as e:
        logging.warning(f"Health: Redis недоступен: {e}")

    status = "ok" if (db_ok and redis_ok) else "degraded"
    http_status = 200 if status == "ok" else 503

    return JSONResponse(
        status_code=http_status,
        content={"status": status, "db": db_ok, "redis": redis_ok},
    )
