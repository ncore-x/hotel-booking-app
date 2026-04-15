import asyncio
import io
import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import TYPE_CHECKING

import bcrypt
import jwt
from fastapi import UploadFile
from PIL import Image, UnidentifiedImageError, ImageFile
from sqlalchemy.exc import NoResultFound

from src.config import settings
from src.exceptions import (
    CorruptedImageException,
    EmptyFileException,
    FileTooLargeException,
    UnsupportedMediaTypeException,
    EmailNotRegisteredException,
    ExpiredTokenException,
    IncorrectPasswordException,
    IncorrectTokenException,
    InvalidRefreshTokenException,
    ObjectAlreadyExistsException,
    ObjectNotFoundException,
    SameEmailException,
    UserAlreadyExistsException,
    UserNotAuthenticatedException,
)
from src.schemas.users import (
    UserEmailUpdate,
    UserPasswordUpdate,
    UserProfileUpdate,
    UserRequestAdd,
    UserAdd,
)
from src.services.base import BaseService
from src.utils.db_manager import DBManager

if TYPE_CHECKING:
    from src.services.token_blacklist import TokenBlacklistService
    from src.services.confirmation import ConfirmationService

logger = logging.getLogger(__name__)


class AuthService(BaseService):
    def __init__(
        self,
        db: DBManager | None = None,
        blacklist: "TokenBlacklistService | None" = None,
        confirmation: "ConfirmationService | None" = None,
    ) -> None:
        super().__init__(db)
        self._blacklist = blacklist
        self._confirmation = confirmation

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
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())

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
        except (NoResultFound, ObjectNotFoundException):
            raise EmailNotRegisteredException()

        if not user.hashed_password or not self.verify_password(
            data.password, user.hashed_password
        ):
            raise IncorrectPasswordException()

        access_token = self.create_access_token({"user_id": user.id, "is_admin": user.is_admin})
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

        if payload is not None and self._blacklist:
            await self._blacklist.add(token, payload)

        if refresh_token:
            await self._blacklist_refresh_token(refresh_token)

    async def _blacklist_refresh_token(self, refresh_token: str) -> None:
        try:
            payload = self.decode_token(refresh_token)
        except (ExpiredTokenException, IncorrectTokenException):
            return
        if self._blacklist:
            await self._blacklist.add(refresh_token, payload)

    async def refresh_access_token(self, refresh_token: str) -> tuple[str, str]:
        """Проверяет refresh токен, выдаёт новый access токен и ротирует refresh токен."""
        try:
            payload = self.decode_token(refresh_token)
        except (ExpiredTokenException, IncorrectTokenException):
            raise InvalidRefreshTokenException()

        if payload.get("type") != "refresh":
            raise InvalidRefreshTokenException()

        if self._blacklist and await self._blacklist.is_blacklisted(refresh_token):
            raise InvalidRefreshTokenException()

        user_id = payload.get("user_id")
        if not user_id:
            raise InvalidRefreshTokenException()

        user = await self.db.users.get_one_or_none(id=user_id)
        if user is None:
            raise InvalidRefreshTokenException()

        if self._blacklist:
            await self._blacklist.add(refresh_token, payload)

        new_access_token = self.create_access_token({"user_id": user_id, "is_admin": user.is_admin})
        new_refresh_token = self.create_refresh_token({"user_id": user_id})
        return new_access_token, new_refresh_token

    async def get_one_or_none_user(self, user_id: int):
        return await self.db.users.get_one_or_none(id=user_id)

    async def update_password(self, user_id: int, data: UserPasswordUpdate) -> None:
        try:
            user = await self.db.users.get_user_with_hashed_password_by_id(user_id)
        except ObjectNotFoundException:
            raise UserNotAuthenticatedException()
        if not user.hashed_password or not self.verify_password(
            data.current_password, user.hashed_password
        ):
            raise IncorrectPasswordException()
        new_hash = self.hash_password(data.new_password)

        if self._confirmation is None:
            # Fallback: apply immediately (used in tests / when confirmation is not injected)
            await self.db.users.update_hashed_password(user_id, new_hash)
            await self.db.commit()
            return

        token = await self._confirmation.create_token("password", user_id, {"new_hash": new_hash})
        from src.tasks.tasks import send_confirmation_email_task
        from src.config import settings

        confirm_url = f"{settings.APP_BASE_URL}/confirm?token={token}"
        send_confirmation_email_task.delay(  # type: ignore[attr-defined]
            to_email=user.email,
            subject="Подтверждение смены пароля",
            confirm_url=confirm_url,
        )

    async def upload_avatar(self, user_id: int, file: UploadFile) -> str:
        """Загружает аватар пользователя. Возвращает имя сохранённого файла."""
        ImageFile.LOAD_TRUNCATED_IMAGES = False

        content_type = (file.content_type or "").lower()
        allowed_types = {"image/jpeg", "image/png", "image/webp"}
        if content_type and content_type not in allowed_types:
            raise UnsupportedMediaTypeException(f"Неподдерживаемый тип файла: {content_type}")

        contents = await file.read()
        if not contents:
            raise EmptyFileException()
        if len(contents) > settings.MAX_IMAGE_SIZE_BYTES:
            raise FileTooLargeException()

        bio = io.BytesIO(contents)
        try:
            img = Image.open(bio)
            img.verify()
        except UnidentifiedImageError:
            raise CorruptedImageException("Файл не является изображением")
        except Exception:
            raise CorruptedImageException()

        bio.seek(0)
        try:
            with Image.open(bio) as img_meta:
                img_format = (img_meta.format or "").lower()
        except Exception:
            raise CorruptedImageException()

        ext = "jpg" if img_format == "jpeg" else img_format
        if not ext or ext not in {"jpeg", "jpg", "png", "webp"}:
            raise UnsupportedMediaTypeException(f"Неподдерживаемый формат: {img_format}")

        # Удаляем старый аватар
        old_filename = await self.db.users.get_avatar_filename(user_id)
        if old_filename:
            old_path = settings.IMAGES_DIR / old_filename
            try:
                await asyncio.to_thread(old_path.unlink, True)
            except Exception as e:
                logger.warning("Не удалось удалить старый аватар %s: %s", old_path, e)

        images_dir = settings.IMAGES_DIR
        images_dir.mkdir(parents=True, exist_ok=True)
        safe_name = f"avatar_{uuid.uuid4().hex}.{ext}"
        image_path = images_dir / safe_name

        def _write():
            with open(image_path, "wb") as fh:
                fh.write(contents)

        try:
            await asyncio.to_thread(_write)
        except Exception as e:
            raise CorruptedImageException(f"Не удалось сохранить файл: {e}")

        await self.db.users.update_avatar(user_id, safe_name)
        await self.db.commit()
        return safe_name

    async def delete_avatar(self, user_id: int) -> None:
        """Удаляет аватар пользователя."""
        filename = await self.db.users.get_avatar_filename(user_id)
        if filename:
            image_path = settings.IMAGES_DIR / filename
            try:
                await asyncio.to_thread(image_path.unlink, True)
            except Exception as e:
                logger.warning("Не удалось удалить файл аватара %s: %s", image_path, e)
        await self.db.users.update_avatar(user_id, None)
        await self.db.commit()

    async def update_profile(self, user_id: int, data: UserProfileUpdate) -> None:
        """Обновляет профильные данные пользователя."""
        await self.db.users.update_profile(user_id, data)
        await self.db.commit()

    async def update_email(self, user_id: int, data: UserEmailUpdate) -> None:
        try:
            user = await self.db.users.get_user_with_hashed_password_by_id(user_id)
        except ObjectNotFoundException:
            raise UserNotAuthenticatedException()
        if not user.hashed_password or not self.verify_password(
            data.current_password, user.hashed_password
        ):
            raise IncorrectPasswordException()
        if user.email == data.new_email:
            raise SameEmailException()

        # Check if new email is already taken
        existing = await self.db.users.get_one_or_none(email=data.new_email)
        if existing is not None:
            raise UserAlreadyExistsException()

        if self._confirmation is None:
            # Fallback: apply immediately (used in tests / when confirmation is not injected)
            try:
                await self.db.users.update_email(user_id, data.new_email)
                await self.db.commit()
            except ObjectAlreadyExistsException:
                raise UserAlreadyExistsException()
            return

        token = await self._confirmation.create_token(
            "email", user_id, {"new_email": data.new_email}
        )
        from src.tasks.tasks import send_confirmation_email_task
        from src.config import settings

        confirm_url = f"{settings.APP_BASE_URL}/confirm?token={token}"
        send_confirmation_email_task.delay(  # type: ignore[attr-defined]
            to_email=data.new_email,
            subject="Подтверждение смены email",
            confirm_url=confirm_url,
        )

    async def confirm_change(self, token: str) -> None:
        """Применяет отложенное изменение пароля или email по токену подтверждения."""
        assert self._confirmation is not None, "ConfirmationService is required"
        payload = await self._confirmation.consume_token(token)

        change_type = payload.get("type")
        user_id = payload.get("user_id")

        if change_type == "password":
            new_hash = payload["new_hash"]
            await self.db.users.update_hashed_password(user_id, new_hash)
            await self.db.commit()
        elif change_type == "email":
            new_email = payload["new_email"]
            try:
                await self.db.users.update_email(user_id, new_email)
                await self.db.commit()
            except ObjectAlreadyExistsException:
                raise UserAlreadyExistsException()
