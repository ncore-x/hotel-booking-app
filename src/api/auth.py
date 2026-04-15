from fastapi import APIRouter, Depends, Request, Response, UploadFile, status

from src.api.dependencies import (
    UserIdDep,
    DBDep,
    get_blacklist_service,
    get_confirmation_service,
    get_oauth_service,
)
from src.config import settings
from src.exceptions import (
    ConfirmationTokenNotFoundException,
    ConfirmationTokenNotFoundHTTPException,
    CorruptedImageException,
    CorruptedImageHTTPException,
    EmptyFileException,
    EmptyFileHTTPException,
    ExpiredTokenException,
    FileTooLargeException,
    FileTooLargeHTTPException,
    IncorrectPasswordHTTPException,
    IncorrectPasswordException,
    EmailNotRegisteredHTTPException,
    EmailNotRegisteredException,
    IncorrectTokenException,
    InvalidOAuthStateException,
    InvalidOAuthStateHTTPException,
    InvalidRefreshTokenException,
    InvalidRefreshTokenHTTPException,
    OAuthEmailConflictException,
    OAuthEmailConflictHTTPException,
    OAuthProviderNotConfiguredException,
    OAuthProviderNotConfiguredHTTPException,
    SameEmailException,
    SameEmailHTTPException,
    UnsupportedMediaTypeException,
    UnsupportedMediaTypeHTTPException,
    UnsupportedOAuthProviderException,
    UnsupportedOAuthProviderHTTPException,
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
    UserProfileUpdate,
    UserRequestAdd,
    User,
    LoginResponse,
)
from src.services.auth import AuthService
from src.services.confirmation import ConfirmationService
from src.services.oauth import OAuthService
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
async def update_password(
    user_id: UserIdDep,
    db: DBDep,
    data: UserPasswordUpdate,
    confirmation: ConfirmationService = Depends(get_confirmation_service),
):
    try:
        await AuthService(db, confirmation=confirmation).update_password(user_id, data)
    except IncorrectPasswordException:
        raise IncorrectPasswordHTTPException()


@router.patch("/me/profile", summary="Обновить профиль", response_model=User)
async def update_profile(user_id: UserIdDep, db: DBDep, data: UserProfileUpdate):
    await AuthService(db).update_profile(user_id, data)
    return await AuthService(db).get_one_or_none_user(user_id)


@router.post("/me/avatar", summary="Загрузить аватар", response_model=User)
async def upload_avatar(user_id: UserIdDep, db: DBDep, file: UploadFile):
    """Загрузка аватара (PNG/JPEG/WebP, макс. 5 МБ)."""
    try:
        await AuthService(db).upload_avatar(user_id, file)
    except EmptyFileException:
        raise EmptyFileHTTPException()
    except FileTooLargeException:
        raise FileTooLargeHTTPException()
    except UnsupportedMediaTypeException:
        raise UnsupportedMediaTypeHTTPException()
    except CorruptedImageException:
        raise CorruptedImageHTTPException()
    return await AuthService(db).get_one_or_none_user(user_id)


@router.delete("/me/avatar", summary="Удалить аватар", status_code=status.HTTP_204_NO_CONTENT)
async def delete_avatar(user_id: UserIdDep, db: DBDep):
    await AuthService(db).delete_avatar(user_id)


@router.patch("/me/email", summary="Изменить email", status_code=status.HTTP_204_NO_CONTENT)
async def update_email(
    user_id: UserIdDep,
    db: DBDep,
    data: UserEmailUpdate,
    confirmation: ConfirmationService = Depends(get_confirmation_service),
):
    try:
        await AuthService(db, confirmation=confirmation).update_email(user_id, data)
    except IncorrectPasswordException:
        raise IncorrectPasswordHTTPException()
    except SameEmailException:
        raise SameEmailHTTPException()
    except UserAlreadyExistsException:
        raise UserEmailAlreadyExistsHTTPException()


@router.get("/confirm", summary="Подтвердить изменение", status_code=status.HTTP_200_OK)
async def confirm_change(
    token: str,
    db: DBDep,
    confirmation: ConfirmationService = Depends(get_confirmation_service),
):
    """Применяет отложенное изменение пароля или email по токену из письма."""
    try:
        await AuthService(db, confirmation=confirmation).confirm_change(token)
    except ConfirmationTokenNotFoundException:
        raise ConfirmationTokenNotFoundHTTPException()
    except UserAlreadyExistsException:
        raise UserEmailAlreadyExistsHTTPException()
    return {"detail": "Изменение подтверждено."}


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
        access_token, new_refresh_token = await AuthService(
            db, blacklist=blacklist
        ).refresh_access_token(token)
    except InvalidRefreshTokenException:
        raise InvalidRefreshTokenHTTPException()
    response.set_cookie(value=access_token, **_COOKIE_KWARGS)
    response.set_cookie(value=new_refresh_token, **_REFRESH_COOKIE_KWARGS)
    return LoginResponse(access_token=access_token, refresh_token=new_refresh_token)


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


# ── OAuth 2.0 ─────────────────────────────────────────────────────────────────


@router.get("/oauth/{provider}/authorize", summary="Получить URL OAuth-провайдера")
async def oauth_authorize(provider: str, oauth: OAuthService = Depends(get_oauth_service)):
    """Возвращает URL для редиректа пользователя на страницу входа OAuth-провайдера."""
    try:
        url = await oauth.create_authorization_url(provider)
    except UnsupportedOAuthProviderException:
        raise UnsupportedOAuthProviderHTTPException()
    except OAuthProviderNotConfiguredException:
        raise OAuthProviderNotConfiguredHTTPException()
    return {"url": url}


@router.post(
    "/oauth/{provider}/callback", summary="Обработать OAuth callback", response_model=LoginResponse
)
async def oauth_callback(
    provider: str,
    response: Response,
    db: DBDep,
    code: str,
    state: str,
):
    """
    Принимает code + state от OAuth-провайдера, создаёт/получает пользователя
    и выдаёт JWT-токены в куках.
    """
    from src.init import redis_manager

    oauth = OAuthService(db=db, redis=redis_manager)
    try:
        user, _ = await oauth.handle_callback(provider, code, state)
    except UnsupportedOAuthProviderException:
        raise UnsupportedOAuthProviderHTTPException()
    except OAuthProviderNotConfiguredException:
        raise OAuthProviderNotConfiguredHTTPException()
    except InvalidOAuthStateException:
        raise InvalidOAuthStateHTTPException()
    except OAuthEmailConflictException:
        raise OAuthEmailConflictHTTPException()

    auth_svc = AuthService(db)
    access_token = auth_svc.create_access_token({"user_id": user.id, "is_admin": user.is_admin})
    refresh_token = auth_svc.create_refresh_token({"user_id": user.id})

    response.set_cookie(value=access_token, **_COOKIE_KWARGS)  # type: ignore[arg-type]
    response.set_cookie(value=refresh_token, **_REFRESH_COOKIE_KWARGS)  # type: ignore[arg-type]
    return LoginResponse(access_token=access_token, refresh_token=refresh_token)
