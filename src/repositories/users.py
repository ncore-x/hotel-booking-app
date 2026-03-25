from pydantic import EmailStr
from sqlalchemy import select, update

from src.repositories.mappers.mappers import UserDataMapper
from src.schemas.users import UserWithHashedPassword
from src.models.users import UsersOrm
from src.repositories.base import BaseRepository


class UsersRepository(BaseRepository):
    model = UsersOrm
    mapper = UserDataMapper

    async def get_user_with_hashed_password(self, email: EmailStr):
        query = select(self.model).filter_by(email=email)
        result = await self.session.execute(query)
        model = result.scalars().one()
        return UserWithHashedPassword.model_validate(model, from_attributes=True)

    async def get_user_with_hashed_password_by_id(self, user_id: int):
        query = select(self.model).filter_by(id=user_id)
        result = await self.session.execute(query)
        model = result.scalars().one()
        return UserWithHashedPassword.model_validate(model, from_attributes=True)

    async def update_hashed_password(self, user_id: int, hashed_password: str) -> None:
        stmt = (
            update(self.model)
            .where(self.model.id == user_id)
            .values(hashed_password=hashed_password)
        )
        await self.session.execute(stmt)
