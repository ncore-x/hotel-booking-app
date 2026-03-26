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
from src.services.token_blacklist import TokenBlacklistService
from src.utils.db_manager import DBManager
from src.database import async_session_maker


class PaginationParams(BaseModel):
    page: Annotated[int, Query(1, ge=1, description="Номер страницы")]
    per_page: Annotated[int, Query(10, ge=1, le=100, description="Элементов на странице")]


PaginationDep = Annotated[PaginationParams, Depends()]


def get_token(request: Request) -> str:
    token = request.cookies.get("access_token", None)
    if not token:
        raise NoAccessTokenHTTPException()
    return token


def get_blacklist_service() -> TokenBlacklistService:
    from src.init import redis_manager

    return TokenBlacklistService(redis=redis_manager)


async def get_current_user_id(
    token: str = Depends(get_token),
    blacklist: TokenBlacklistService = Depends(get_blacklist_service),
) -> int:
    try:
        payload = AuthService().decode_token(token)
    except ExpiredTokenException:
        raise ExpiredTokenHTTPException()
    except IncorrectTokenException:
        raise IncorrectTokenHTTPException()

    if await blacklist.is_blacklisted(token):
        raise ExpiredTokenHTTPException()

    if payload.get("type") != "access":
        raise IncorrectTokenHTTPException()

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
    user_id: int = Depends(get_current_user_id),
    token: str = Depends(get_token),
) -> int:
    """Проверяет is_admin из JWT payload (без SELECT к БД)."""
    payload = AuthService().decode_token(token)
    if not payload.get("is_admin"):
        raise InsufficientPermissionsHTTPException()
    return user_id


AdminDep = Annotated[int, Depends(get_current_admin)]
