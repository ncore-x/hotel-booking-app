import logging
from datetime import datetime, timezone, timedelta

import jwt
from passlib.context import CryptContext
from sqlalchemy.exc import NoResultFound

from src.config import settings
from src.exceptions import (
    ExpiredTokenException,
    IncorrectPasswordException,
    IncorrectTokenException,
    InvalidRefreshTokenException,
    EmailNotRegisteredException,
    ObjectAlreadyExistsException,
    UserAlreadyExistsException,
    UserNotAuthenticatedException,
)
from src.schemas.users import UserPasswordUpdate, UserRequestAdd, UserAdd
from src.services.base import BaseService


class AuthService(BaseService):
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def create_access_token(self, data: dict) -> str:
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        to_encode |= {"exp": expire, "type": "access"}
        return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    def create_refresh_token(self, data: dict) -> str:
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode |= {"exp": expire, "type": "refresh"}
        return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    def hash_password(self, password: str) -> str:
        return self.pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return self.pwd_context.verify(plain_password, hashed_password)

    def decode_token(self, token: str) -> dict:
        """Декодирует токен. При неудаче пробует JWT_SECRET_KEY_PREVIOUS (ротация ключей)."""
        try:
            return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        except jwt.ExpiredSignatureError:
            raise ExpiredTokenException()
        except jwt.InvalidTokenError:
            if settings.JWT_SECRET_KEY_PREVIOUS:
                try:
                    return jwt.decode(
                        token,
                        settings.JWT_SECRET_KEY_PREVIOUS,
                        algorithms=[settings.JWT_ALGORITHM],
                    )
                except jwt.ExpiredSignatureError:
                    raise ExpiredTokenException()
                except jwt.InvalidTokenError:
                    pass
            raise IncorrectTokenException()

    async def register_user(self, data: UserRequestAdd):
        hashed_password = self.hash_password(data.password)
        new_user_data = UserAdd(email=data.email, hashed_password=hashed_password)
        try:
            user = await self.db.users.add(new_user_data)
            await self.db.commit()
            return user
        except ObjectAlreadyExistsException as ex:
            raise UserAlreadyExistsException from ex

    async def login_user(self, data: UserRequestAdd) -> tuple[str, str]:
        try:
            user = await self.db.users.get_user_with_hashed_password(email=data.email)
        except NoResultFound:
            raise EmailNotRegisteredException()

        if not self.verify_password(data.password, user.hashed_password):
            raise IncorrectPasswordException()

        access_token = self.create_access_token({"user_id": user.id})
        refresh_token = self.create_refresh_token({"user_id": user.id})
        return access_token, refresh_token

    async def logout_user(self, token: str, refresh_token: str | None = None) -> None:
        """
        Инвалидирует access и refresh токены, занося их в Redis-блэклист.
        Если access токен уже истёк — выход разрешён без ошибки.
        Если access токен невалиден — считаем пользователя не аутентифицированным.
        """
        if not token:
            raise UserNotAuthenticatedException()

        try:
            payload = self.decode_token(token)
        except ExpiredTokenException:
            payload = None
        except IncorrectTokenException:
            raise UserNotAuthenticatedException()

        if payload is not None:
            exp = payload.get("exp", 0)
            ttl = max(1, int(exp - datetime.now(timezone.utc).timestamp()))
            try:
                from src.init import redis_manager

                await redis_manager.set(f"blacklist:{token}", "1", expire=ttl)
            except Exception as e:
                logging.warning(f"Не удалось занести токен в блэклист Redis: {e}")

        if refresh_token:
            await self._blacklist_refresh_token(refresh_token)

    async def _blacklist_refresh_token(self, refresh_token: str) -> None:
        try:
            payload = self.decode_token(refresh_token)
            exp = payload.get("exp", 0)
            ttl = max(1, int(exp - datetime.now(timezone.utc).timestamp()))
            from src.init import redis_manager

            await redis_manager.set(f"blacklist:{refresh_token}", "1", expire=ttl)
        except (ExpiredTokenException, IncorrectTokenException):
            pass
        except Exception as e:
            logging.warning(f"Не удалось занести refresh токен в блэклист Redis: {e}")

    async def refresh_access_token(self, refresh_token: str) -> str:
        """Проверяет refresh токен и выдаёт новый access токен."""
        try:
            payload = self.decode_token(refresh_token)
        except ExpiredTokenException:
            raise InvalidRefreshTokenException()
        except IncorrectTokenException:
            raise InvalidRefreshTokenException()

        if payload.get("type") != "refresh":
            raise InvalidRefreshTokenException()

        try:
            from src.init import redis_manager

            if redis_manager.redis and await redis_manager.exists(f"blacklist:{refresh_token}"):
                raise InvalidRefreshTokenException()
        except InvalidRefreshTokenException:
            raise
        except Exception as e:
            logging.warning(f"Не удалось проверить блэклист refresh токена: {e}")

        user_id = payload.get("user_id")
        if not user_id:
            raise InvalidRefreshTokenException()

        return self.create_access_token({"user_id": user_id})

    async def get_one_or_none_user(self, user_id: int):
        return await self.db.users.get_one_or_none(id=user_id)

    async def update_password(self, user_id: int, data: UserPasswordUpdate) -> None:
        user = await self.db.users.get_user_with_hashed_password_by_id(user_id)
        if not self.verify_password(data.current_password, user.hashed_password):
            raise IncorrectPasswordException()
        new_hash = self.hash_password(data.new_password)
        await self.db.users.update_hashed_password(user_id, new_hash)
        await self.db.commit()
