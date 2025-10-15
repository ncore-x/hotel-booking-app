# fmt: off
# ruff: noqa: E402
import json
import pytest
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from unittest import mock

mock.patch("fastapi_cache.decorator.cache",
           lambda *args, **kwargs: lambda f: f).start()

from src.utils.db_manager import DBManager
from src.schemas.rooms import RoomAdd
from src.schemas.hotels import HotelAdd
from src.models import * # noqa
from src.main import app
from src.database import Base, engine_null_pool, async_session_maker_null_pool
from src.config import settings
from src.api.dependencies import get_db


@pytest.fixture(scope="session", autouse=True)
def check_test_mode():
    assert settings.MODE == "TEST"


async def get_db_null_pool():
    async with DBManager(session_factory=async_session_maker_null_pool) as db:
        yield db


@pytest.fixture(scope="function")
async def db() -> AsyncGenerator[DBManager, None]:
    async for db in get_db_null_pool():
        yield db


app.dependency_overrides[get_db] = get_db_null_pool


@pytest.fixture(scope="session", autouse=True)
async def setup_database(check_test_mode):
    async with engine_null_pool.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    with open("tests/mock_hotels.json", encoding="utf-8") as file_hotels:
        hotels = json.load(file_hotels)
    with open("tests/mock_rooms.json", encoding="utf-8") as file_rooms:
        rooms = json.load(file_rooms)

    hotels = [HotelAdd.model_validate(hotel) for hotel in hotels]
    rooms = [RoomAdd.model_validate(room) for room in rooms]

    async with DBManager(session_factory=async_session_maker_null_pool) as db_:
        await db_.hotels.add_bulk(hotels)
        await db_.rooms.add_bulk(rooms)
        await db_.commit()


@pytest.fixture(scope="session")
async def ac() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture(scope="session", autouse=True)
async def register_user(ac: AsyncClient, setup_database):
    response = await ac.post(
        "/auth/register",
        json={
            "email": "test@example.com",
            "password": "TestPassword123"
        }
    )
    assert response.status_code == 200, f"Registration failed: {response.text}"

@pytest.fixture(scope="session")
async def authenticated_ac(register_user, ac: AsyncClient):
    response = await ac.post(
        "/auth/login",
        json={
            "email": "test@example.com",
            "password": "TestPassword123"
        }
    )

    print("=== AUTHENTICATED_AC LOGIN ===")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    print(f"Cookies: {dict(ac.cookies)}")
    print("==============================")

    assert response.status_code == 200, f"Login failed: {response.text}"
    assert ac.cookies["access_token"], "No access token in cookies"

    yield ac

# fmt: on
