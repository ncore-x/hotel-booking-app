from datetime import date

from src.schemas.bookings import BookingAdd, Booking
from src.utils.db_manager import DBManager


async def test_booking_crud(db: DBManager):
    user_id = (await db.users.get_all())[0].id  # type: ignore
    room_id = (await db.rooms.get_all())[0].id  # type: ignore
    booking_data = BookingAdd(
        user_id=user_id,
        room_id=room_id,
        date_from=date(year=2025, month=1, day=1),
        date_to=date(year=2025, month=1, day=2),
        price=100,
    )
    new_booking: Booking = await db.bookings.add(booking_data)

    # получить эту бронь и убедиться что она есть
    booking: Booking | None = await db.bookings.get_one_or_none(id=new_booking.id)
    assert booking
    assert booking.id == new_booking.id
    assert booking.room_id == new_booking.room_id
    assert booking.user_id == new_booking.user_id
    assert booking.model_dump(exclude={"id"}) == booking_data.model_dump()

    # обновить бронь
    update_date = date(year=2025, month=1, day=20)
    update_booking_data = BookingAdd(
        user_id=user_id,
        room_id=room_id,
        date_from=date(year=2025, month=8, day=10),
        date_to=update_date,
        price=100,
    )
    await db.bookings.edit(update_booking_data, id=new_booking.id)
    update_booking: Booking | None = await db.bookings.get_one_or_none(id=new_booking.id)
    assert update_booking
    assert update_booking.id == new_booking.id
    assert update_booking.date_to == update_date

    # удалить бронь
    await db.bookings.delete(id=new_booking.id)
    booking: Booking | None = await db.bookings.get_one_or_none(id=new_booking.id)
    assert not booking
