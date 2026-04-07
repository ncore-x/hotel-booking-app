import logging
from contextlib import asynccontextmanager
from pathlib import Path

import sentry_sdk
import uvicorn
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.routing import APIRoute
from fastapi.staticfiles import StaticFiles
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.requests import Request
from starlette.responses import Response

from src.middleware.prometheus import PrometheusMiddleware
from src.tracing import setup_tracing

from src.api.auth import router as router_auth
from src.api.bookings import router as router_bookings
from src.api.facilities import router as router_facilities
from src.api.health import router as router_health
from src.api.hotels import router as router_hotels
from src.api.images import router as router_images
from src.api.rooms import router as router_rooms
from src.exception_handlers import validation_exception_handler
from src.init import redis_manager
from src.elastic.client import init_es, close_es
from src.elastic import hotels as es_hotels
from src.limiter import limiter
from src.config import settings
from src.logging_config import setup_logging
from src.middleware.json_error_handler import JSONErrorHandlerMiddleware
from src.middleware.request_id import RequestIDMiddleware

setup_logging(level=settings.LOG_LEVEL, json_format=settings.LOG_JSON)

if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.SENTRY_ENVIRONMENT,
        traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
        send_default_pii=False,
    )
    logging.info("Sentry инициализирован (env=%s)", settings.SENTRY_ENVIRONMENT)


def generate_unique_id(route: APIRoute) -> str:
    return route.name


openapi_tags = [
    {"name": "Auth", "description": "Регистрация, вход, выход и профиль пользователя."},
    {
        "name": "Hotels",
        "description": "Поиск и управление отелями. Фильтрация по датам.",
    },
    {
        "name": "Rooms",
        "description": "Номера отеля. Вложенный ресурс: `/api/v1/hotels/{hotel_id}/rooms`.",
    },
    {"name": "Bookings", "description": "Создание, просмотр и отмена бронирований."},
    {
        "name": "Facilities",
        "description": "Справочник удобств (Wi-Fi, бассейн, парковка и т.д.).",
    },
    {"name": "Images", "description": "Загрузка изображений отелей."},
]


async def _es_startup() -> None:
    """Init Elasticsearch and reindex all hotels. Best-effort — errors don't block startup."""
    es = await init_es()
    if es is None:
        return
    try:
        from src.utils.db_manager import DBManager
        from src.database import async_session_maker_null_pool

        async with DBManager(session_factory=async_session_maker_null_pool) as db:
            all_hotels = await db.hotels.get_all()

        hotels_data = [
            {"id": h.id, "title": h.title, "city": h.city, "address": h.address} for h in all_hotels
        ]
        await es_hotels.reindex_all(es, hotels_data)
    except Exception as exc:
        logging.warning("ES startup reindex failed: %s", exc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await redis_manager.connect()
        if not await redis_manager.ping():
            raise ConnectionError("Redis не отвечает на ping")
        FastAPICache.init(RedisBackend(redis_manager.redis), prefix="fastapi-cache")
        logging.info("Cache: Redis backend")
    except Exception as e:
        logging.warning(f"Redis недоступен, включается InMemory-кеш: {e}")
        from fastapi_cache.backends.inmemory import InMemoryBackend

        FastAPICache.init(InMemoryBackend(), prefix="fastapi-cache")

    await _es_startup()

    yield

    await redis_manager.close()
    await close_es()


_docs_url = None if settings.MODE == "PROD" else "/docs"
_redoc_url = None if settings.MODE == "PROD" else "/redoc"
_openapi_url = None if settings.MODE == "PROD" else "/openapi.json"

app = FastAPI(
    lifespan=lifespan,
    generate_unique_id_function=generate_unique_id,
    title="Hotel Booking API",
    description=(
        "REST API для поиска и бронирования отелей.\n\n"
        "Все эндпоинты находятся под префиксом `/api/v1`.\n\n"
        "Операции записи (POST/PUT/PATCH/DELETE) для отелей, номеров и удобств "
        "требуют роли **администратора** (`is_admin=true`)."
    ),
    version="1.0.0",
    contact={"name": "Support", "email": "support@hotelbooking.example"},
    license_info={"name": "MIT"},
    openapi_tags=openapi_tags,
    docs_url=_docs_url,
    redoc_url=_redoc_url,
    openapi_url=_openapi_url,
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(JSONErrorHandlerMiddleware)
app.add_middleware(RequestIDMiddleware)

if settings.OTEL_ENABLED:
    from src.database import engine, engine_null_pool

    setup_tracing(app, engine, engine_null_pool)

if settings.METRICS_ENABLED:
    app.add_middleware(PrometheusMiddleware, app_name="hotel_booking")

    @app.get("/metrics", include_in_schema=False)
    async def metrics(request: Request) -> Response:
        if settings.METRICS_TOKEN:
            auth = request.headers.get("Authorization", "")
            if auth != f"Bearer {settings.METRICS_TOKEN}":
                return Response(status_code=401)
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


BASE_DIR = Path(__file__).parent
static_dir = BASE_DIR / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")

app.add_exception_handler(RequestValidationError, validation_exception_handler)

API_V1 = "/api/v1"
app.include_router(router_health, prefix=API_V1)
app.include_router(router_auth, prefix=API_V1)
app.include_router(router_hotels, prefix=API_V1)
app.include_router(router_rooms, prefix=API_V1)
app.include_router(router_facilities, prefix=API_V1)
app.include_router(router_bookings, prefix=API_V1)
app.include_router(router_images, prefix=API_V1)

if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", reload=True)
