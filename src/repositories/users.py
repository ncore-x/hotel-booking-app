import logging

from pydantic import EmailStr
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError, NoResultFound

from src.exceptions import ObjectAlreadyExistsException, ObjectNotFoundException
from src.repositories.mappers.mappers import UserDataMapper
from src.schemas.users import UserOAuthAdd, UserProfileUpdate, User, UserWithHashedPassword
from src.models.users import UsersOrm
from src.repositories.base import BaseRepository

try:
    from asyncpg import UniqueViolationError
except ImportError:
    UniqueViolationError = None  # type: ignore[assignment,misc]


class UsersRepository(BaseRepository):
    model = UsersOrm
    mapper = UserDataMapper

    async def get_user_with_hashed_password(self, email: EmailStr):
        query = select(self.model).filter_by(email=email)
        result = await self.session.execute(query)
        try:
            model = result.scalars().one()
        except NoResultFound:
            raise ObjectNotFoundException()
        return UserWithHashedPassword.model_validate(model, from_attributes=True)

    async def get_user_with_hashed_password_by_id(self, user_id: int):
        query = select(self.model).filter_by(id=user_id)
        result = await self.session.execute(query)
        try:
            model = result.scalars().one()
        except NoResultFound:
            raise ObjectNotFoundException()
        return UserWithHashedPassword.model_validate(model, from_attributes=True)

    async def update_hashed_password(self, user_id: int, hashed_password: str) -> None:
        stmt = (
            update(self.model)
            .where(self.model.id == user_id)
            .values(hashed_password=hashed_password)
        )
        await self.session.execute(stmt)

    async def update_avatar(self, user_id: int, filename: str | None) -> None:
        """Устанавливает или удаляет аватар пользователя."""
        stmt = update(self.model).where(self.model.id == user_id).values(avatar_filename=filename)
        await self.session.execute(stmt)

    async def get_avatar_filename(self, user_id: int) -> str | None:
        """Возвращает текущий avatar_filename пользователя."""
        query = select(self.model.avatar_filename).where(self.model.id == user_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def update_profile(self, user_id: int, data: UserProfileUpdate) -> None:
        """Обновляет поля профиля пользователя. None-значения не применяются."""
        values = {k: v for k, v in data.model_dump().items() if v is not None}
        if not values:
            return
        stmt = update(self.model).where(self.model.id == user_id).values(**values)
        await self.session.execute(stmt)

    async def update_email(self, user_id: int, new_email: str) -> None:
        stmt = update(self.model).where(self.model.id == user_id).values(email=new_email)
        try:
            await self.session.execute(stmt)
        except IntegrityError as ex:
            logging.exception("Email uniqueness violation: %s", ex)
            if UniqueViolationError and isinstance(ex.orig.__cause__, UniqueViolationError):
                raise ObjectAlreadyExistsException() from ex
            raise

    async def get_by_oauth(self, provider: str, oauth_id: str) -> User | None:
        """Возвращает пользователя по OAuth-провайдеру и идентификатору или None."""
        query = select(self.model).where(
            self.model.oauth_provider == provider,
            self.model.oauth_id == oauth_id,
        )
        result = await self.session.execute(query)
        model = result.scalars().one_or_none()
        if model is None:
            return None
        return User.model_validate(model, from_attributes=True)

    async def link_oauth(
        self, user_id: int, provider: str, oauth_id: str, avatar_url: str | None
    ) -> None:
        """Привязывает OAuth-провайдер к существующему пользователю."""
        stmt = (
            update(self.model)
            .where(self.model.id == user_id)
            .values(oauth_provider=provider, oauth_id=oauth_id, oauth_avatar_url=avatar_url)
        )
        await self.session.execute(stmt)

    async def create_oauth_user(self, data: UserOAuthAdd) -> User:
        """Создаёт нового пользователя через OAuth (без пароля)."""
        orm_obj = self.model(
            email=data.email,
            hashed_password=None,
            oauth_provider=data.oauth_provider,
            oauth_id=data.oauth_id,
            oauth_avatar_url=data.oauth_avatar_url,
            first_name=data.first_name,
        )
        self.session.add(orm_obj)
        await self.session.flush()
        return User.model_validate(orm_obj, from_attributes=True)
