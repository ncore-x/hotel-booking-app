from fastapi import APIRouter, Request, Response, status

from src.api.dependencies import UserIdDep, DBDep
from src.config import settings
from src.exceptions import (
    ExpiredTokenException,
    IncorrectPasswordHTTPException,
    IncorrectPasswordException,
    EmailNotRegisteredHTTPException,
    EmailNotRegisteredException,
    IncorrectTokenException,
    UserAlreadyExistsException,
    UserEmailAlreadyExistsHTTPException,
    UserIsAlreadyAuthenticatedHTTPException,
    UserNotAuthenticatedException,
    UserNotAuthenticatedHTTPException,
)
from src.limiter import limiter
from src.schemas.users import UserPasswordUpdate, UserRequestAdd, User, LoginResponse
from src.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])

_COOKIE_KWARGS = dict(
    key="access_token",
    httponly=True,
    samesite="lax",
    secure=settings.COOKIE_SECURE,
)


@router.post(
    "/register",
    summary="Регистрация пользователя",
    response_model=User,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit(settings.AUTH_RATE_LIMIT)
async def register_user(request: Request, response: Response, data: UserRequestAdd, db: DBDep):
    try:
        user = await AuthService(db).register_user(data)
    except UserAlreadyExistsException:
        raise UserEmailAlreadyExistsHTTPException()
    response.headers["Location"] = str(request.url_for("get_me"))
    return user


@router.post("/login", summary="Вход в систему", response_model=LoginResponse)
@limiter.limit(settings.AUTH_RATE_LIMIT)
async def login_user(request: Request, response: Response, data: UserRequestAdd, db: DBDep):
    token = request.cookies.get("access_token")
    if token:
        try:
            AuthService(db).decode_token(token)
            raise UserIsAlreadyAuthenticatedHTTPException()
        except (ExpiredTokenException, IncorrectTokenException):
            pass

    try:
        access_token = await AuthService(db).login_user(data)
    except EmailNotRegisteredException:
        raise EmailNotRegisteredHTTPException()
    except IncorrectPasswordException:
        raise IncorrectPasswordHTTPException()

    response.set_cookie(value=access_token, **_COOKIE_KWARGS)
    return LoginResponse(access_token=access_token)


@router.get("/me", summary="Текущий пользователь", response_model=User)
async def get_me(user_id: UserIdDep, db: DBDep):
    return await AuthService(db).get_one_or_none_user(user_id)


@router.patch("/me", summary="Изменить пароль", status_code=status.HTTP_204_NO_CONTENT)
async def update_password(user_id: UserIdDep, db: DBDep, data: UserPasswordUpdate):
    try:
        await AuthService(db).update_password(user_id, data)
    except IncorrectPasswordException:
        raise IncorrectPasswordHTTPException()


@router.post("/logout", summary="Выход из системы", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response, request: Request, db: DBDep):
    token = request.cookies.get("access_token")
    try:
        await AuthService(db).logout_user(token)
    except UserNotAuthenticatedException:
        raise UserNotAuthenticatedHTTPException()
    response.delete_cookie(
        key="access_token",
        httponly=True,
        samesite="lax",
        secure=settings.COOKIE_SECURE,
    )
