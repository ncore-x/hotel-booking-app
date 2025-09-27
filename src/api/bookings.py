from fastapi import APIRouter
from fastapi_cache.decorator import cache

from src.api.dependencies import DBDep, UserIdDep
from src.schemas.bookings import BookingAddRequest, BookingAdd
from src.schemas.hotels import Hotel
from src.schemas.rooms import Room

router = APIRouter(prefix="/bookings", tags=["Бронирования"])


@router.get("", summary="Получение бронирований")
@cache(expire=10)
async def get_bookings(db: DBDep):
    return await db.bookings.get_all()


@router.get("/me", summary="Получение моих бронирований")
@cache(expire=10)
async def get_my_bookings(db: DBDep, user_id: UserIdDep):
    return await db.bookings.get_filtered(user_id=user_id)


@router.post("", summary="Создать новое бронирование")
async def add_booking(
    user_id: UserIdDep,
    db: DBDep,
    booking_data: BookingAddRequest,
):
    room: Room | None = await db.rooms.get_one_or_none(id=booking_data.room_id)
    hotel: Hotel | None = await db.hotels.get_one_or_none(id=room.hotel_id)
    room_price: int = room.price
    _booking_data = BookingAdd(
        user_id=user_id,
        price=room_price,
        **booking_data.model_dump(),
    )
    booking = await db.bookings.add_booking(_booking_data, hotel_id=hotel.id)
    await db.commit()
    return {"status": "OK", "data": booking}
