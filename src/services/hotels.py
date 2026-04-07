import logging
import math
from datetime import date

from src.exceptions import (
    CannotDeleteHotelWithRoomsException,
    HotelNotFoundException,
    ObjectNotFoundException,
    check_date_to_after_date_from,
)
from src.schemas.common import PaginatedResponse
from src.schemas.hotels import Hotel, HotelAdd, HotelPatch
from src.services.base import BaseService
from src.elastic.client import get_es_client
from src.elastic import hotels as es_hotels

logger = logging.getLogger(__name__)


class HotelService(BaseService):
    async def get_filtered_by_time(
        self,
        pagination,
        city: str | None,
        title: str | None,
        date_from: date | None,
        date_to: date | None,
        sort_by: str = "id",
        order: str = "asc",
        guests: int = 1,
        search: str | None = None,
    ) -> PaginatedResponse[Hotel]:
        if date_from and date_to:
            check_date_to_after_date_from(date_from, date_to)
        per_page = pagination.per_page
        offset = per_page * (pagination.page - 1)

        items, total = (
            await self.db.hotels.get_filtered_by_time(
                date_from=date_from,
                date_to=date_to,
                city=city,
                title=title,
                search=search,
                limit=per_page,
                offset=offset,
                sort_by=sort_by,
                order=order,
                guests=guests,
            ),
            await self.db.hotels.count_filtered_by_time(
                date_from=date_from,
                date_to=date_to,
                city=city,
                title=title,
                search=search,
                guests=guests,
            ),
        )

        return PaginatedResponse(
            items=items,
            total=total,
            page=pagination.page,
            per_page=per_page,
            pages=max(1, math.ceil(total / per_page)),
        )

    async def get_hotel(self, hotel_id: int):
        return await self.db.hotels.get_one(id=hotel_id)

    async def add_hotel(self, data: HotelAdd):
        # Rely on the DB unique constraint (uq_hotels_title_city_address).
        # BaseRepository.add() catches UniqueViolationError → ObjectAlreadyExistsException.
        hotel = await self.db.hotels.add(data)
        await self.db.commit()
        await self._es_index(hotel.id, hotel.title, hotel.city, hotel.address)
        return hotel

    async def hotel_put_update(self, hotel_id: int, data: HotelAdd) -> Hotel:
        await self.get_hotel_with_check(hotel_id)
        await self.db.hotels.edit(data, id=hotel_id)
        await self.db.commit()
        hotel = await self.get_hotel(hotel_id)
        await self._es_index(hotel.id, hotel.title, hotel.city, hotel.address)
        return hotel

    async def hotel_patch_update(
        self, hotel_id: int, data: HotelPatch, exclude_unset: bool = False
    ) -> Hotel:
        await self.get_hotel_with_check(hotel_id)
        await self.db.hotels.edit(data, exclude_unset=exclude_unset, id=hotel_id)
        await self.db.commit()
        hotel = await self.get_hotel(hotel_id)
        await self._es_index(hotel.id, hotel.title, hotel.city, hotel.address)
        return hotel

    async def delete_hotel(self, hotel_id: int):
        await self.get_hotel_with_check(hotel_id)
        rooms_count = await self.db.rooms.count_by_hotel(hotel_id)
        if rooms_count > 0:
            raise CannotDeleteHotelWithRoomsException()
        await self.db.hotels.delete(id=hotel_id)
        await self.db.commit()
        await self._es_remove(hotel_id)

    async def get_hotel_with_check(self, hotel_id: int) -> Hotel:
        try:
            return await self.db.hotels.get_one(id=hotel_id)
        except ObjectNotFoundException:
            raise HotelNotFoundException()

    async def autocomplete_combined(self, q: str) -> dict:
        es = get_es_client()
        if es is not None:
            try:
                return await es_hotels.autocomplete(es, q)
            except Exception as exc:
                logger.warning("ES autocomplete failed, fallback to PG: %s", exc)
        return await self.db.hotels.get_autocomplete_combined(q)

    async def _es_index(self, hotel_id: int, title: str, city: str, address: str | None) -> None:
        es = get_es_client()
        if es is None:
            return
        try:
            await es_hotels.index_hotel(es, hotel_id, title, city, address)
        except Exception as exc:
            logger.warning("ES index failed for hotel %d: %s", hotel_id, exc)

    async def popular_locations(self, limit: int = 8) -> list[str]:
        return await self.db.hotels.get_popular_locations(limit)

    async def _es_remove(self, hotel_id: int) -> None:
        es = get_es_client()
        if es is None:
            return
        try:
            await es_hotels.remove_hotel(es, hotel_id)
        except Exception as exc:
            logger.warning("ES delete failed for hotel %d: %s", hotel_id, exc)
