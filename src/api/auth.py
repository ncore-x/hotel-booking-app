from fastapi import APIRouter, HTTPException, Response
from fastapi_cache.decorator import cache

from src.exceptions import ObjectAlreadyExistsException
from src.api.dependencies import DBDep, UserIdDep
from src.services.auth import AuthService
from src.schemas.users import UserAdd, UserRequestAdd

router = APIRouter(prefix="/auth", tags=["Авторизация и аутентификация"])


@router.post("/register", summary="Регистрация пользователя")
async def register_user(data: UserRequestAdd, db: DBDep):
    hashed_password = AuthService().hash_password(data.password)
    new_user_data = UserAdd(email=data.email, hashed_password=hashed_password)
    try:
        await db.users.add(new_user_data)
        await db.commit()
    except ObjectAlreadyExistsException:
        raise HTTPException(
            status_code=409, detail="Пользователь с такой почтой уже существует")
    return {"status": "OK"}


@router.post("/login", summary="Авторизация пользователя")
async def login_user(data: UserRequestAdd, response: Response, db: DBDep):
    user = await db.users.get_user_with_hashed_password(email=data.email)
    if not user:
        raise HTTPException(
            status_code=401, detail="Пользователь с таким email не зарегистрирован")
    if not AuthService().verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Пароль неверный")
    access_token = AuthService().create_access_token({"user_id": user.id})
    response.set_cookie("access_token", access_token)
    return {"access_token": access_token}


@router.get("/me", summary="Получение текущего аутентифицированного пользователя")
@cache(expire=10)
async def get_me(user_id: UserIdDep, db: DBDep):
    user = await db.users.get_one_or_none(id=user_id)
    return user


@router.post("/logout", summary="Выход из текущего аккаунта")
async def logout(response: Response):
    response.delete_cookie("access_token")
    return {"status": "Ok"}
