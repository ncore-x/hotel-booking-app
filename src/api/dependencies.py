from typing import Annotated
from fastapi import Depends, Query, Request
from pydantic import BaseModel

from src.exceptions import (
    ExpiredTokenHTTPException,
    IncorrectTokenException,
    IncorrectTokenHTTPException,
    NoAccessTokenHTTPException,
    ExpiredTokenException,
)
from src.services.auth import AuthService
from src.utils.db_manager import DBManager
from src.database import async_session_maker


class PaginationParams(BaseModel):
    page: Annotated[int, Query(1, ge=1)]
    per_page: Annotated[int | None, Query(None, ge=1, lt=30)]


PaginationDep = Annotated[PaginationParams, Depends()]


def get_token(request: Request) -> str:
    token = request.cookies.get("access_token", None)
    if not token:
        raise NoAccessTokenHTTPException()
    return token


def get_current_user_id(
        token: str = Depends(get_token),
        db: DBManager = Depends(lambda: DBManager(session_factory=async_session_maker))) -> int:
    try:
        payload = AuthService(db).decode_token(token)
    except ExpiredTokenException:
        raise ExpiredTokenHTTPException
    except IncorrectTokenException:
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
