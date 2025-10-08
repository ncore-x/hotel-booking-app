from fastapi import APIRouter, Depends, Request, Response

from src.api.dependencies import UserIdDep, DBDep
from src.exceptions import ExpiredTokenException, IncorrectPasswordHTTPException, IncorrectPasswordException, \
    EmailNotRegisteredHTTPException, EmailNotRegisteredException, IncorrectTokenException, UserAlreadyExistsException, \
    UserEmailAlreadyExistsHTTPException, UserIsAlreadyAuthenticatedHTTPException, UserNotAuthenticatedException, UserNotAuthenticatedHTTPException
from src.schemas.users import UserRequestAdd
from src.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["Авторизация и аутентификация"])


@router.post("/register")
async def register_user(
    data: UserRequestAdd,
    db: DBDep,
):
    try:
        await AuthService(db).register_user(data)
    except UserAlreadyExistsException:
        raise UserEmailAlreadyExistsHTTPException

    return {"detail": "Вы успешно зарегистрировались!"}


@router.post("/login")
async def login_user(
    data: UserRequestAdd,
    response: Response,
    request: Request,
    db: DBDep,
):
    token = request.cookies.get("access_token")
    if token:
        try:
            AuthService(db).decode_token(token)
            raise UserIsAlreadyAuthenticatedHTTPException()
        except ExpiredTokenException:
            pass
        except IncorrectTokenException:
            pass

    try:
        access_token = await AuthService(db).login_user(data)
    except EmailNotRegisteredException:
        raise EmailNotRegisteredHTTPException
    except IncorrectPasswordException:
        raise IncorrectPasswordHTTPException

    response.set_cookie("access_token", access_token)
    return {"detail": "Успешный вход в систему!", "access_token": access_token}


@router.get("/me")
async def get_me(
    user_id: UserIdDep,
    db: DBDep,
):
    return await AuthService(db).get_one_or_none_user(user_id)


@router.post("/logout", response_model=None)
async def logout(response: Response, request: Request, db: DBDep):
    token = request.cookies.get("access_token")
    try:
        await AuthService(db).logout_user(token)
    except UserNotAuthenticatedException:
        raise UserNotAuthenticatedHTTPException

    response.delete_cookie("access_token")
    return {"detail": "Вы вышли из системы!"}
