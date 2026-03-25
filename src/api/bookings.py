from fastapi import APIRouter, Query, Request, Response, status

from src.services.bookings import BookingService
from src.exceptions import (
    AllRoomsAreBookedException,
    AllRoomsAreBookedHTTPException,
    InvalidDateRangeException,
    InvalidDateRangeHTTPException,
    RoomNotFoundException,
    RoomNotFoundHTTPException,
    ObjectNotFoundException,
    ObjectNotFoundHTTPException,
)
from src.api.dependencies import DBDep, UserIdDep
from src.schemas.bookings import Booking, BookingAddRequest, BookingPatchRequest
from src.schemas.common import PaginatedResponse

router = APIRouter(prefix="/bookings", tags=["Bookings"])


@router.get("/me", summary="Мои бронирования", response_model=PaginatedResponse[Booking])
async def get_my_bookings(
    db: DBDep,
    user_id: UserIdDep,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    return await BookingService(db).get_my_bookings(user_id, page=page, per_page=per_page)


@router.get("/{booking_id}", summary="Бронирование по ID", response_model=Booking)
async def get_booking(booking_id: int, user_id: UserIdDep, db: DBDep):
    try:
        return await BookingService(db).get_booking(user_id, booking_id)
    except ObjectNotFoundException:
        raise ObjectNotFoundHTTPException()


@router.post(
    "",
    summary="Создать бронирование",
    response_model=Booking,
    status_code=status.HTTP_201_CREATED,
)
async def add_booking(
    user_id: UserIdDep,
    db: DBDep,
    request: Request,
    response: Response,
    booking_data: BookingAddRequest,
):
    try:
        booking = await BookingService(db).add_booking(user_id, booking_data)
    except RoomNotFoundException:
        raise RoomNotFoundHTTPException()
    except AllRoomsAreBookedException:
        raise AllRoomsAreBookedHTTPException()
    response.headers["Location"] = str(request.url_for("get_my_bookings"))
    return booking


@router.patch("/{booking_id}", summary="Изменить даты бронирования", response_model=Booking)
async def patch_booking(
    booking_id: int, user_id: UserIdDep, db: DBDep, data: BookingPatchRequest
):
    try:
        return await BookingService(db).patch_booking(user_id, booking_id, data)
    except ObjectNotFoundException:
        raise ObjectNotFoundHTTPException()
    except InvalidDateRangeException:
        raise InvalidDateRangeHTTPException()
    except AllRoomsAreBookedException:
        raise AllRoomsAreBookedHTTPException()


@router.delete(
    "/{booking_id}",
    summary="Отменить бронирование",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def cancel_booking(booking_id: int, user_id: UserIdDep, db: DBDep):
    try:
        await BookingService(db).cancel_booking(user_id, booking_id)
    except ObjectNotFoundException:
        raise ObjectNotFoundHTTPException()
