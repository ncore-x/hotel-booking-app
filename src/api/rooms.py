from datetime import date

from fastapi import APIRouter, Body, Query, Request, Response, status
from fastapi_cache.decorator import cache

from src.services.rooms import RoomService
from src.exceptions import (
    CannotDeleteRoomWithBookingsException,
    CannotDeleteRoomWithBookingsHTTPException,
    HotelNotFoundException,
    HotelNotFoundHTTPException,
    InvalidDateRangeException,
    InvalidDateRangeHTTPException,
    RoomNotFoundException,
    RoomNotFoundHTTPException,
    ObjectNotFoundException,
    ObjectNotFoundHTTPException,
    ObjectAlreadyExistsException,
    ObjectAlreadyExistsHTTPException,
)
from src.api.dependencies import DBDep, PaginationDep, AdminDep
from src.schemas.common import PaginatedResponse
from src.schemas.rooms import RoomAddRequest, RoomPatchRequest, RoomWithRels

router = APIRouter(prefix="/hotels", tags=["Rooms"])


@router.get(
    "/{hotel_id}/rooms",
    summary="Доступные номера",
    response_model=PaginatedResponse[RoomWithRels],
)
@cache(expire=10)
async def get_rooms(
    hotel_id: int,
    pagination: PaginationDep,
    db: DBDep,
    date_from: date | None = Query(None, examples=["2025-09-01"]),
    date_to: date | None = Query(None, examples=["2025-09-15"]),
):
    try:
        return await RoomService(db).get_filtered_by_time(
            hotel_id, date_from, date_to, pagination.page, pagination.per_page
        )
    except HotelNotFoundException:
        raise HotelNotFoundHTTPException()
    except InvalidDateRangeException:
        raise InvalidDateRangeHTTPException()


@router.get(
    "/{hotel_id}/rooms/{room_id}",
    summary="Получить номер",
    response_model=RoomWithRels,
)
@cache(expire=10)
async def get_room(hotel_id: int, room_id: int, db: DBDep):
    try:
        return await RoomService(db).get_room(room_id, hotel_id=hotel_id)
    except HotelNotFoundException:
        raise HotelNotFoundHTTPException()
    except RoomNotFoundException:
        raise RoomNotFoundHTTPException()


@router.post(
    "/{hotel_id}/rooms",
    summary="Создать номер",
    response_model=RoomWithRels,
    status_code=status.HTTP_201_CREATED,
)
async def create_room(
    _: AdminDep,
    hotel_id: int,
    request: Request,
    response: Response,
    db: DBDep,
    room_data: RoomAddRequest = Body(),
):
    try:
        room = await RoomService(db).create_room(hotel_id, room_data)
    except HotelNotFoundException:
        raise HotelNotFoundHTTPException()
    except ObjectNotFoundException:
        raise ObjectNotFoundHTTPException()
    except ObjectAlreadyExistsException:
        raise ObjectAlreadyExistsHTTPException()
    response.headers["Location"] = str(
        request.url_for("get_room", hotel_id=hotel_id, room_id=room.id)
    )
    return room


@router.put(
    "/{hotel_id}/rooms/{room_id}",
    summary="Полное обновление номера",
    response_model=RoomWithRels,
)
async def room_put_update(
    _: AdminDep, hotel_id: int, room_id: int, room_data: RoomAddRequest, db: DBDep
):
    try:
        return await RoomService(db).room_put_update(hotel_id, room_id, room_data)
    except HotelNotFoundException:
        raise HotelNotFoundHTTPException()
    except RoomNotFoundException:
        raise RoomNotFoundHTTPException()
    except ObjectNotFoundException:
        raise ObjectNotFoundHTTPException()
    except ObjectAlreadyExistsException:
        raise ObjectAlreadyExistsHTTPException()


@router.patch(
    "/{hotel_id}/rooms/{room_id}",
    summary="Частичное обновление номера",
    response_model=RoomWithRels,
)
async def room_patch_update(
    _: AdminDep, hotel_id: int, room_id: int, room_data: RoomPatchRequest, db: DBDep
):
    try:
        return await RoomService(db).room_patch_update(hotel_id, room_id, room_data)
    except HotelNotFoundException:
        raise HotelNotFoundHTTPException()
    except RoomNotFoundException:
        raise RoomNotFoundHTTPException()
    except ObjectNotFoundException:
        raise ObjectNotFoundHTTPException()
    except ObjectAlreadyExistsException:
        raise ObjectAlreadyExistsHTTPException()


@router.delete(
    "/{hotel_id}/rooms/{room_id}",
    summary="Удалить номер",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_room(_: AdminDep, hotel_id: int, room_id: int, db: DBDep):
    try:
        await RoomService(db).delete_room(hotel_id, room_id)
    except HotelNotFoundException:
        raise HotelNotFoundHTTPException()
    except RoomNotFoundException:
        raise RoomNotFoundHTTPException()
    except CannotDeleteRoomWithBookingsException:
        raise CannotDeleteRoomWithBookingsHTTPException()
