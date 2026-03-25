from datetime import date
from sqlalchemy import select, func

from src.repositories.mappers.mappers import HotelDataMapper
from src.models.rooms import RoomsOrm
from src.repositories.base import BaseRepository
from src.models.hotels import HotelsOrm
from src.repositories.utils import rooms_ids_for_booking
from src.schemas.hotels import Hotel


class HotelsRepository(BaseRepository):
    model = HotelsOrm
    mapper = HotelDataMapper

    def _base_query(self, date_from: date, date_to: date, location=None, title=None):
        rooms_ids_to_get = rooms_ids_for_booking(date_from=date_from, date_to=date_to)
        hotels_ids_to_get = (
            select(RoomsOrm.hotel_id)
            .select_from(RoomsOrm)
            .filter(RoomsOrm.id.in_(rooms_ids_to_get))
        )
        query = select(HotelsOrm).filter(HotelsOrm.id.in_(hotels_ids_to_get))
        if location:
            query = query.filter(
                func.lower(HotelsOrm.location).contains(location.strip().lower())
            )
        if title:
            query = query.filter(
                func.lower(HotelsOrm.title).contains(title.strip().lower())
            )
        return query

    async def get_filtered_by_time(
        self,
        date_from: date,
        date_to: date,
        location=None,
        title=None,
        limit=None,
        offset=None,
        sort_by: str = "id",
        order: str = "asc",
    ) -> list[Hotel]:
        query = self._base_query(date_from, date_to, location, title)
        column = getattr(HotelsOrm, sort_by, HotelsOrm.id)
        query = query.order_by(column.asc() if order == "asc" else column.desc())
        query = query.limit(limit).offset(offset)
        result = await self.session.execute(query)
        return [
            self.mapper.map_to_domain_entity(hotel) for hotel in result.scalars().all()
        ]

    async def count_filtered_by_time(
        self,
        date_from: date,
        date_to: date,
        location=None,
        title=None,
    ) -> int:
        base = self._base_query(date_from, date_to, location, title)
        count_query = select(func.count()).select_from(base.subquery())
        result = await self.session.execute(count_query)
        return result.scalar_one()
