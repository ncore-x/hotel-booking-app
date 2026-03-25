import math
from datetime import date

from src.exceptions import (
    CannotDeleteHotelWithRoomsException,
    HotelNotFoundException,
    ObjectAlreadyExistsException,
    ObjectNotFoundException,
    check_date_to_after_date_from,
)
from src.schemas.common import PaginatedResponse
from src.schemas.hotels import Hotel, HotelAdd, HotelPatch
from src.services.base import BaseService


class HotelService(BaseService):
    async def get_filtered_by_time(
        self,
        pagination,
        location: str | None,
        title: str | None,
        date_from: date,
        date_to: date,
        sort_by: str = "id",
        order: str = "asc",
    ) -> PaginatedResponse[Hotel]:
        check_date_to_after_date_from(date_from, date_to)
        per_page = pagination.per_page
        offset = per_page * (pagination.page - 1)

        items, total = await self.db.hotels.get_filtered_by_time(
            date_from=date_from,
            date_to=date_to,
            location=location,
            title=title,
            limit=per_page,
            offset=offset,
            sort_by=sort_by,
            order=order,
        ), await self.db.hotels.count_filtered_by_time(
            date_from=date_from,
            date_to=date_to,
            location=location,
            title=title,
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
        # Rely on the DB unique constraint (uq_hotels_title_location).
        # BaseRepository.add() catches UniqueViolationError → ObjectAlreadyExistsException.
        hotel = await self.db.hotels.add(data)
        await self.db.commit()
        return hotel

    async def hotel_put_update(self, hotel_id: int, data: HotelAdd) -> Hotel:
        await self.get_hotel_with_check(hotel_id)
        try:
            await self.db.hotels.edit(data, id=hotel_id)
        except Exception as ex:
            from asyncpg import UniqueViolationError
            from sqlalchemy.exc import IntegrityError

            if isinstance(ex, IntegrityError) and isinstance(
                ex.orig.__cause__, UniqueViolationError
            ):
                raise ObjectAlreadyExistsException from ex
            raise
        await self.db.commit()
        return await self.get_hotel(hotel_id)

    async def hotel_patch_update(
        self, hotel_id: int, data: HotelPatch, exclude_unset: bool = False
    ) -> Hotel:
        await self.get_hotel_with_check(hotel_id)
        try:
            await self.db.hotels.edit(data, exclude_unset=exclude_unset, id=hotel_id)
        except Exception as ex:
            from asyncpg import UniqueViolationError
            from sqlalchemy.exc import IntegrityError

            if isinstance(ex, IntegrityError) and isinstance(
                ex.orig.__cause__, UniqueViolationError
            ):
                raise ObjectAlreadyExistsException from ex
            raise
        await self.db.commit()
        return await self.get_hotel(hotel_id)

    async def delete_hotel(self, hotel_id: int):
        await self.get_hotel_with_check(hotel_id)
        rooms_count = await self.db.rooms.count_by_hotel(hotel_id)
        if rooms_count > 0:
            raise CannotDeleteHotelWithRoomsException()
        await self.db.hotels.delete(id=hotel_id)
        await self.db.commit()

    async def get_hotel_with_check(self, hotel_id: int) -> Hotel:
        try:
            return await self.db.hotels.get_one(id=hotel_id)
        except ObjectNotFoundException:
            raise HotelNotFoundException()
