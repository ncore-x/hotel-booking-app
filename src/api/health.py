import asyncio
import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text

from src.config import settings
from src.database import engine_null_pool as _engine

router = APIRouter(prefix="/health", tags=["System"])

_DB_TIMEOUT = 2.0
_REDIS_TIMEOUT = 2.0


async def _check_db() -> bool:
    try:
        async with _engine.connect() as conn:
            await asyncio.wait_for(conn.execute(text("SELECT 1")), timeout=_DB_TIMEOUT)
        return True
    except Exception as e:
        logging.warning(f"Health: DB недоступна: {e}")
        return False


async def _check_redis() -> bool:
    try:
        from src.init import redis_manager

        return await asyncio.wait_for(redis_manager.ping(), timeout=_REDIS_TIMEOUT)
    except Exception as e:
        logging.warning(f"Health: Redis недоступен: {e}")
        return False


@router.api_route("/live", methods=["GET", "HEAD"], summary="Liveness probe", include_in_schema=False)
async def liveness():
    """
    Liveness probe: процесс жив и отвечает.
    Не проверяет внешние зависимости — только то, что приложение запущено.
    Используется Docker healthcheck и K8s livenessProbe.
    """
    return JSONResponse(
        status_code=200,
        content={"status": "live", "version": settings.APP_VERSION},
    )


@router.get("", summary="Readiness check", include_in_schema=False)
async def health():
    """
    Readiness probe: проверяет доступность базы данных и Redis.
    Возвращает 503 если хотя бы одна зависимость недоступна.
    Используется мониторингом и K8s readinessProbe.
    """
    db_ok, redis_ok = await asyncio.gather(_check_db(), _check_redis())

    status = "ok" if (db_ok and redis_ok) else "degraded"
    http_status = 200 if status == "ok" else 503

    return JSONResponse(
        status_code=http_status,
        content={"status": status, "db": db_ok, "redis": redis_ok, "version": settings.APP_VERSION},
    )
