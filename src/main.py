# fmt: off
import uvicorn
import sys
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from pathlib import Path
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi.staticfiles import StaticFiles

sys.path.append(str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO)

from src.init import redis_manager
from src.api.auth import router as router_auth
from src.api.hotels import router as router_hotels
from src.api.rooms import router as router_rooms
from src.api.bookings import router as router_bookings
from src.api.facilities import router as router_facilities
from src.api.images import router as router_images
from src.exception_handlers import validation_exception_handler
from src.middleware.json_error_handler import JSONErrorHandlerMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    await redis_manager.connect()
    FastAPICache.init(RedisBackend(redis_manager._redis), prefix="fastapi-cache")
    logging.info("FastAPI cache initialized")
    yield
    await redis_manager.close()


app = FastAPI(lifespan=lifespan)

BASE_DIR = Path(__file__).parent
static_dir = BASE_DIR / "static"

app.mount("/static", StaticFiles(directory=static_dir), name="static")

app.add_middleware(JSONErrorHandlerMiddleware)

app.add_exception_handler(RequestValidationError, validation_exception_handler)

app.include_router(router_auth)
app.include_router(router_hotels)
app.include_router(router_rooms)
app.include_router(router_facilities)
app.include_router(router_bookings)
app.include_router(router_images)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", reload=True)

# fmt: on
