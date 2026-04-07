from datetime import date

from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import NoResultFound

from src.exceptions import RoomNotFoundException
from src.repositories.mappers.mappers import RoomDataMapper, RoomDataWithRelsMapper
from src.repositories.base import BaseRepository
from src.models.rooms import RoomsOrm
from src.repositories.utils import rooms_ids_for_booking


class RoomsRepository(BaseRepository):
    model: type[RoomsOrm] = RoomsOrm
    mapper = RoomDataMapper

    def _available_ids_query(self, hotel_id: int, date_from: date, date_to: date):
        return rooms_ids_for_booking(date_from, date_to, hotel_id)

    async def get_filtered_by_time(
        self,
        hotel_id: int,
        date_from: date | None,
        date_to: date | None,
        limit: int | None = None,
        offset: int = 0,
    ):
        query = select(self.model).options(selectinload(self.model.facilities))
        if date_from and date_to:
            rooms_ids_to_get = self._available_ids_query(hotel_id, date_from, date_to)
            query = query.filter(RoomsOrm.id.in_(rooms_ids_to_get))
        else:
            query = query.filter(RoomsOrm.hotel_id == hotel_id)
        query = query.limit(limit).offset(offset)
        result = await self.session.execute(query)
        return [
            RoomDataWithRelsMapper.map_to_domain_entity(model) for model in result.scalars().all()
        ]

    async def count_filtered_by_time(self, hotel_id: int, date_from: date | None, date_to: date | None) -> int:
        if date_from and date_to:
            rooms_ids_to_get = self._available_ids_query(hotel_id, date_from, date_to)
            base = select(self.model).filter(RoomsOrm.id.in_(rooms_ids_to_get))
        else:
            base = select(self.model).filter(RoomsOrm.hotel_id == hotel_id)
        count_query = select(func.count()).select_from(base.subquery())
        result = await self.session.execute(count_query)
        return result.scalar_one()

    async def count_by_hotel(self, hotel_id: int) -> int:
        query = select(func.count()).where(RoomsOrm.hotel_id == hotel_id)
        result = await self.session.execute(query)
        return result.scalar_one()

    async def get_one_with_rels(self, **filter_by):
        query = (
            select(self.model).options(selectinload(self.model.facilities)).filter_by(**filter_by)
        )
        result = await self.session.execute(query)
        try:
            model = result.scalar_one()
        except NoResultFound:
            raise RoomNotFoundException()
        return RoomDataWithRelsMapper.map_to_domain_entity(model)

    async def get_by_fields(
        self,
        hotel_id: int,
        title: str,
        description: str | None,
        price: int,
        quantity: int,
    ):
        query = select(self.model).filter(
            and_(
                self.model.hotel_id == hotel_id,
                self.model.title == title,
                self.model.price == price,
                self.model.quantity == quantity,
                self.model.description == description,
            )
        )
        result = await self.session.execute(query)
        model = result.scalars().first()
        if not model:
            return None
        return RoomDataMapper.map_to_domain_entity(model)
