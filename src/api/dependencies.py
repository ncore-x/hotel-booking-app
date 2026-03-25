import logging
from typing import Annotated

from fastapi import Depends, Query, Request

from pydantic import BaseModel

from src.exceptions import (
    ExpiredTokenHTTPException,
    IncorrectTokenException,
    IncorrectTokenHTTPException,
    NoAccessTokenHTTPException,
    ExpiredTokenException,
    InsufficientPermissionsHTTPException,
)
from src.services.auth import AuthService
from src.utils.db_manager import DBManager
from src.database import async_session_maker


class PaginationParams(BaseModel):
    page: Annotated[int, Query(1, ge=1, description="Номер страницы")]
    per_page: Annotated[
        int, Query(10, ge=1, le=100, description="Элементов на странице")
    ]


PaginationDep = Annotated[PaginationParams, Depends()]


def get_token(request: Request) -> str:
    token = request.cookies.get("access_token", None)
    if not token:
        raise NoAccessTokenHTTPException()
    return token


async def get_current_user_id(token: str = Depends(get_token)) -> int:
    try:
        payload = AuthService().decode_token(token)
    except ExpiredTokenException:
        raise ExpiredTokenHTTPException()
    except IncorrectTokenException:
        raise IncorrectTokenHTTPException()

    # JWT blacklist check (Redis)
    try:
        from src.init import redis_manager

        if redis_manager.redis and await redis_manager.exists(f"blacklist:{token}"):
            raise ExpiredTokenHTTPException()
    except ExpiredTokenHTTPException:
        raise
    except Exception as e:
        logging.warning(f"Не удалось проверить блэклист токенов: {e}")

    user_id = payload.get("user_id")
    if not user_id:
        raise IncorrectTokenHTTPException()
    return user_id


UserIdDep = Annotated[int, Depends(get_current_user_id)]


async def get_db():
    async with DBManager(session_factory=async_session_maker) as db:
        yield db


DBDep = Annotated[DBManager, Depends(get_db)]


async def get_current_admin(
    user_id: int = Depends(get_current_user_id), db: DBManager = Depends(get_db)
) -> int:
    """Проверяет, что текущий пользователь является администратором."""
    user = await db.users.get_one_or_none(id=user_id)
    if not user or not user.is_admin:
        raise InsufficientPermissionsHTTPException()
    return user_id


AdminDep = Annotated[int, Depends(get_current_admin)]
