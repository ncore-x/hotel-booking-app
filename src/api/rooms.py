from datetime import date
from fastapi import APIRouter, Body, Query
from fastapi_cache.decorator import cache

from src.services.rooms import RoomService
from src.exceptions import (
    CannotDeleteRoomWithBookingsException,
    CannotDeleteRoomWithBookingsHTTPException,
    HotelNotFoundException,
    HotelNotFoundHTTPException,
    RoomNotFoundException,
    RoomNotFoundHTTPException,
    ObjectNotFoundException,
    ObjectNotFoundHTTPException,
    ObjectAlreadyExistsException,
    ObjectAlreadyExistsHTTPException,
    InvalidDateRangeException,
    InvalidDateRangeHTTPException,
)
from src.api.dependencies import DBDep
from src.schemas.rooms import RoomAddRequest, RoomPatchRequest

router = APIRouter(prefix="/hotels", tags=["Номера"])


@router.get("/{hotel_id}/rooms", summary="Получение номеров")
@cache(expire=10)
async def get_rooms(
    hotel_id: int,
    db: DBDep,
    date_from: date = Query(example="2025-09-01"),
    date_to: date = Query(example="2025-09-15"),
):
    try:
        rooms = await RoomService(db).get_filtered_by_time(
            hotel_id,
            date_from,
            date_to,
        )
    except HotelNotFoundException:
        raise HotelNotFoundHTTPException
    except InvalidDateRangeException:
        raise InvalidDateRangeHTTPException
    return {"detail": "Номера успешно получены!", "data": rooms}


@router.get("/{hotel_id}/rooms/{room_id}", summary="Получение номера")
@cache(expire=10)
async def get_room(hotel_id: int, room_id: int, db: DBDep):
    try:
        room = await RoomService(db).get_room(room_id, hotel_id=hotel_id)
    except HotelNotFoundException:
        raise HotelNotFoundHTTPException
    except RoomNotFoundException:
        raise RoomNotFoundHTTPException
    return {"detail": "Номер успешно получен!", "data": room}


@router.post("/{hotel_id}/rooms", summary="Создание нового номера")
async def create_room(hotel_id: int, db: DBDep, room_data: RoomAddRequest = Body()):
    try:
        room = await RoomService(db).create_room(hotel_id, room_data)
    except HotelNotFoundException:
        raise HotelNotFoundHTTPException
    except ObjectNotFoundException:
        raise ObjectNotFoundHTTPException
    except ObjectAlreadyExistsException:
        raise ObjectAlreadyExistsHTTPException
    return {"detail": "Номер успешно добавлен!", "data": room}


@router.put(
    "/{hotel_id}/rooms/{room_id}",
    summary="Обновление номера",
    description="Полное обновление данных по номеру",
)
async def room_put_update(hotel_id: int, room_id: int, room_data: RoomAddRequest, db: DBDep):
    try:
        await RoomService(db).room_put_update(hotel_id, room_id, room_data)
    except HotelNotFoundException:
        raise HotelNotFoundHTTPException
    except RoomNotFoundException:
        raise RoomNotFoundHTTPException
    except ObjectNotFoundException:
        raise ObjectNotFoundHTTPException
    except ObjectAlreadyExistsException:
        raise ObjectAlreadyExistsHTTPException()
    return {"detail": "Изменения успешно сохранены!"}


@router.patch("/{hotel_id}/rooms/{room_id}", summary="Частичное обновление отеля")
async def room_patch_update(hotel_id: int, room_id: int, room_data: RoomPatchRequest, db: DBDep):
    try:
        await RoomService(db).room_patch_update(hotel_id, room_id, room_data)
    except HotelNotFoundException:
        raise HotelNotFoundHTTPException
    except RoomNotFoundException:
        raise RoomNotFoundHTTPException
    except ObjectNotFoundException:
        raise ObjectNotFoundHTTPException
    except ObjectAlreadyExistsException:
        raise ObjectAlreadyExistsHTTPException
    return {"detail": "Изменения успешно сохранены!"}


@router.delete("/{hotel_id}/rooms/{room_id}", summary="Удаление номера")
async def delete_room(hotel_id: int, room_id: int, db: DBDep):
    try:
        await RoomService(db).delete_room(hotel_id, room_id)
    except HotelNotFoundException:
        raise HotelNotFoundHTTPException()
    except RoomNotFoundException:
        raise RoomNotFoundHTTPException()
    except CannotDeleteRoomWithBookingsException:
        raise CannotDeleteRoomWithBookingsHTTPException()

    return {"detail": "Номер успешно удалён!"}
