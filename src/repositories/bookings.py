from datetime import date, datetime, timezone
from typing import Sequence

from sqlalchemy import select, func

from src.exceptions import AllRoomsAreBookedException
from src.repositories.utils import rooms_ids_for_booking
from src.schemas.bookings import BookingAdd
from src.models.bookings import BookingsOrm
from src.models.rooms import RoomsOrm
from src.repositories.base import BaseRepository
from src.repositories.mappers.mappers import BookingDataMapper


class BookingsRepository(BaseRepository):
    model = BookingsOrm
    mapper = BookingDataMapper

    async def get_bookings_with_today_checkin(self):
        today = datetime.now(tz=timezone.utc).date()
        query = select(BookingsOrm).filter(BookingsOrm.date_from == today)
        res = await self.session.execute(query)
        return [self.mapper.map_to_domain_entity(booking) for booking in res.scalars().all()]

    async def count_by_user(self, user_id: int) -> int:
        query = select(func.count()).where(BookingsOrm.user_id == user_id)
        result = await self.session.execute(query)
        return result.scalar_one()

    async def count_by_room(self, room_id: int) -> int:
        query = select(func.count()).where(BookingsOrm.room_id == room_id)
        result = await self.session.execute(query)
        return result.scalar_one()

    async def get_paginated_by_user(self, user_id: int, limit: int, offset: int):
        query = (
            select(self.model)
            .where(BookingsOrm.user_id == user_id)
            .order_by(BookingsOrm.date_from.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(query)
        return [self.mapper.map_to_domain_entity(b) for b in result.scalars().all()]

    async def add_booking(self, data: BookingAdd, hotel_id: int):
        # Lock the room row to prevent concurrent overbooking.
        # Other transactions trying to book the same room will wait
        # until this transaction commits, then re-check availability.
        lock_result = await self.session.execute(
            select(RoomsOrm).where(RoomsOrm.id == data.room_id).with_for_update()
        )
        if lock_result.scalar_one_or_none() is None:
            raise AllRoomsAreBookedException

        rooms_ids_to_get = rooms_ids_for_booking(
            date_from=data.date_from,
            date_to=data.date_to,
            hotel_id=hotel_id,
        )
        rooms_ids_to_book_res = await self.session.execute(rooms_ids_to_get)
        rooms_ids_to_book: Sequence[int] = rooms_ids_to_book_res.scalars().all()
        if data.room_id in rooms_ids_to_book:
            new_booking = await self.add(data)
            return new_booking
        raise AllRoomsAreBookedException
