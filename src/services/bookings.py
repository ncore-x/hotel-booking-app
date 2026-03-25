import math

from src.exceptions import (
    InvalidDateRangeException,
    ObjectNotFoundException,
    RoomNotFoundException,
    check_date_to_after_date_from,
)
from src.schemas.bookings import Booking, BookingAdd, BookingAddRequest, BookingPatchRequest
from src.schemas.common import PaginatedResponse
from src.schemas.hotels import Hotel
from src.schemas.rooms import Room
from src.services.base import BaseService


class BookingService(BaseService):
    async def add_booking(self, user_id: int, booking_data: BookingAddRequest):
        try:
            room: Room = await self.db.rooms.get_one(id=booking_data.room_id)
        except ObjectNotFoundException as ex:
            raise RoomNotFoundException from ex

        hotel: Hotel = await self.db.hotels.get_one(id=room.hotel_id)

        _booking_data = BookingAdd(
            user_id=user_id,
            price=room.price,
            **booking_data.model_dump(),
        )

        booking = await self.db.bookings.add_booking(_booking_data, hotel_id=hotel.id)
        await self.db.commit()
        return booking

    async def get_my_bookings(
        self, user_id: int, page: int = 1, per_page: int = 20
    ) -> PaginatedResponse[Booking]:
        total = await self.db.bookings.count_by_user(user_id)
        items = await self.db.bookings.get_paginated_by_user(
            user_id=user_id,
            limit=per_page,
            offset=per_page * (page - 1),
        )
        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            per_page=per_page,
            pages=max(1, math.ceil(total / per_page)),
        )

    async def get_booking(self, user_id: int, booking_id: int) -> Booking:
        booking = await self.db.bookings.get_one_or_none(id=booking_id, user_id=user_id)
        if booking is None:
            raise ObjectNotFoundException()
        return booking

    async def cancel_booking(self, user_id: int, booking_id: int) -> None:
        booking = await self.db.bookings.get_one_or_none(id=booking_id, user_id=user_id)
        if booking is None:
            raise ObjectNotFoundException()
        await self.db.bookings.delete(id=booking_id, user_id=user_id)
        await self.db.commit()

    async def patch_booking(
        self, user_id: int, booking_id: int, data: BookingPatchRequest
    ) -> Booking:
        booking = await self.db.bookings.get_one_or_none(id=booking_id, user_id=user_id)
        if booking is None:
            raise ObjectNotFoundException()

        new_date_from = data.date_from if data.date_from is not None else booking.date_from
        new_date_to = data.date_to if data.date_to is not None else booking.date_to

        check_date_to_after_date_from(new_date_from, new_date_to)

        room: Room = await self.db.rooms.get_one(id=booking.room_id)
        hotel: Hotel = await self.db.hotels.get_one(id=room.hotel_id)

        # Delete old booking within this transaction so the availability
        # re-check sees the freed slot. If add_booking raises, the transaction
        # rolls back and the original booking is preserved.
        await self.db.bookings.delete(id=booking_id, user_id=user_id)

        new_booking_data = BookingAdd(
            user_id=user_id,
            room_id=booking.room_id,
            date_from=new_date_from,
            date_to=new_date_to,
            price=room.price,
        )
        new_booking = await self.db.bookings.add_booking(new_booking_data, hotel_id=hotel.id)
        await self.db.commit()
        return new_booking
