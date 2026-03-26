from fastapi import APIRouter, Depends, Request, Response, status

from src.api.dependencies import UserIdDep, DBDep, get_blacklist_service
from src.config import settings
from src.exceptions import (
    ExpiredTokenException,
    IncorrectPasswordHTTPException,
    IncorrectPasswordException,
    EmailNotRegisteredHTTPException,
    EmailNotRegisteredException,
    IncorrectTokenException,
    InvalidRefreshTokenException,
    InvalidRefreshTokenHTTPException,
    SameEmailException,
    SameEmailHTTPException,
    UserAlreadyExistsException,
    UserEmailAlreadyExistsHTTPException,
    UserIsAlreadyAuthenticatedHTTPException,
    UserNotAuthenticatedException,
    UserNotAuthenticatedHTTPException,
)
from src.limiter import limiter
from src.schemas.users import (
    UserEmailUpdate,
    UserPasswordUpdate,
    UserRequestAdd,
    User,
    LoginResponse,
)
from src.services.auth import AuthService
from src.services.token_blacklist import TokenBlacklistService

router = APIRouter(prefix="/auth", tags=["Auth"])

_COOKIE_KWARGS = dict(
    key="access_token",
    httponly=True,
    samesite="lax",
    secure=settings.COOKIE_SECURE,
)

_REFRESH_COOKIE_KWARGS = dict(
    key="refresh_token",
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
        access_token, refresh_token = await AuthService(db).login_user(data)
    except EmailNotRegisteredException:
        raise EmailNotRegisteredHTTPException()
    except IncorrectPasswordException:
        raise IncorrectPasswordHTTPException()

    response.set_cookie(value=access_token, **_COOKIE_KWARGS)
    response.set_cookie(value=refresh_token, **_REFRESH_COOKIE_KWARGS)
    return LoginResponse(access_token=access_token, refresh_token=refresh_token)


@router.get("/me", summary="Текущий пользователь", response_model=User)
async def get_me(user_id: UserIdDep, db: DBDep):
    return await AuthService(db).get_one_or_none_user(user_id)


@router.patch("/me", summary="Изменить пароль", status_code=status.HTTP_204_NO_CONTENT)
async def update_password(user_id: UserIdDep, db: DBDep, data: UserPasswordUpdate):
    try:
        await AuthService(db).update_password(user_id, data)
    except IncorrectPasswordException:
        raise IncorrectPasswordHTTPException()


@router.patch("/me/email", summary="Изменить email", status_code=status.HTTP_204_NO_CONTENT)
async def update_email(user_id: UserIdDep, db: DBDep, data: UserEmailUpdate):
    try:
        await AuthService(db).update_email(user_id, data)
    except IncorrectPasswordException:
        raise IncorrectPasswordHTTPException()
    except SameEmailException:
        raise SameEmailHTTPException()
    except UserAlreadyExistsException:
        raise UserEmailAlreadyExistsHTTPException()


@router.post("/refresh", summary="Обновить access токен", response_model=LoginResponse)
async def refresh_token(
    request: Request,
    response: Response,
    db: DBDep,
    blacklist: TokenBlacklistService = Depends(get_blacklist_service),
):
    token = request.cookies.get("refresh_token")
    if not token:
        raise InvalidRefreshTokenHTTPException()
    try:
        access_token = await AuthService(db, blacklist=blacklist).refresh_access_token(token)
    except InvalidRefreshTokenException:
        raise InvalidRefreshTokenHTTPException()
    response.set_cookie(value=access_token, **_COOKIE_KWARGS)
    return LoginResponse(access_token=access_token, refresh_token=token)


@router.post("/logout", summary="Выход из системы", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    request: Request,
    db: DBDep,
    blacklist: TokenBlacklistService = Depends(get_blacklist_service),
):
    token = request.cookies.get("access_token")
    refresh = request.cookies.get("refresh_token")
    try:
        await AuthService(db, blacklist=blacklist).logout_user(token, refresh)
    except UserNotAuthenticatedException:
        raise UserNotAuthenticatedHTTPException()
    response.delete_cookie(
        key="access_token", httponly=True, samesite="lax", secure=settings.COOKIE_SECURE
    )
    response.delete_cookie(
        key="refresh_token", httponly=True, samesite="lax", secure=settings.COOKIE_SECURE
    )
