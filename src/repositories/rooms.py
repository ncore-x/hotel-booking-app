from datetime import date
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import NoResultFound

from src.exceptions import RoomNotFoundException
from src.repositories.mappers.mappers import RoomDataMapper, RoomDataWithRelsMapper
from src.repositories.base import BaseRepository
from src.models.rooms import RoomsOrm
from src.repositories.utils import rooms_ids_for_booking


class RoomsRepository(BaseRepository):
    model: RoomsOrm = RoomsOrm
    mapper = RoomDataMapper

    async def get_filtered_by_time(
        self,
        hotel_id,
        date_from: date,
        date_to: date,
    ):
        rooms_ids_to_get = rooms_ids_for_booking(date_from, date_to, hotel_id)

        if isinstance(rooms_ids_to_get, (list, tuple, set)):
            if not rooms_ids_to_get:
                return []

        query = (
            select(self.model)  # type: ignore
            .options(selectinload(self.model.facilities))
            .filter(RoomsOrm.id.in_(rooms_ids_to_get))  # type: ignore
        )
        result = await self.session.execute(query)
        return [
            RoomDataWithRelsMapper.map_to_domain_entity(model) for model in result.scalars().all()
        ]

    async def get_one_with_rels(self, **filter_by):
        query = (
            select(self.model).options(selectinload(self.model.facilities)).filter_by(**filter_by)  # type: ignore
        )
        result = await self.session.execute(query)
        try:
            model = result.scalar_one()
        except NoResultFound:
            raise RoomNotFoundException
        return RoomDataWithRelsMapper.map_to_domain_entity(model)

    async def get_by_fields(
        self, hotel_id: int, title: str, description: str | None, price: int, quantity: int
    ):
        query = select(self.model).filter(
            and_(
                self.model.hotel_id == hotel_id,
                self.model.title == title,
                self.model.price == price,
                self.model.quantity == quantity,
                (self.model.description == description),
            )
        )
        result = await self.session.execute(query)
        model = result.scalars().first()
        if not model:
            return None
        return RoomDataMapper.map_to_domain_entity(model)
