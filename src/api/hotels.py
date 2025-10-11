from datetime import date
from fastapi import Query, APIRouter, Body
from fastapi_cache.decorator import cache

from src.services.hotels import HotelService
from src.exceptions import (
    CannotDeleteHotelWithRoomsException,
    CannotDeleteHotelWithRoomsHTTPException,
    HotelNotFoundException,
    HotelNotFoundHTTPException,
    ObjectNotFoundException,
    ObjectAlreadyExistsException,
    ObjectAlreadyExistsHTTPException
)
from src.api.dependencies import PaginationDep, DBDep
from src.schemas.hotels import HotelPatch, HotelAdd

router = APIRouter(prefix="/hotels", tags=["Отели"])


@router.get("", summary="Получение отелей")
@cache(expire=10)
async def get_hotels(
    pagination: PaginationDep,
    db: DBDep,
    location: str | None = Query(None, description="Локация"),
    title: str | None = Query(None, description="Название отеля"),
    date_from: date = Query(example="2025-09-01"),
    date_to: date = Query(example="2025-09-15"),
):
    return await HotelService(db).get_filtered_by_time(
        pagination,
        location,
        title,
        date_from,
        date_to,
    )


@router.get("/{hotel_id}", summary="Получение отеля")
@cache(expire=10)
async def get_hotel(hotel_id: int, db: DBDep):
    try:
        return await HotelService(db).get_hotel(hotel_id)
    except ObjectNotFoundException:
        raise HotelNotFoundHTTPException()


@router.post("", summary="Создание нового отеля")
async def create_hotel(
    db: DBDep,
    hotel_data: HotelAdd = Body(
        openapi_examples={
            "1": {
                "summary": "Сочи",
                "value": {
                    "title": "Апартаменты Brevis Rents",
                    "location": "Сочи, ул. Орджоникидзе, д. 11/1",
                },
            },
            "2": {
                "summary": "Дубай",
                "value": {
                    "title": "Signature 1 Hotel Tecom",
                    "location": "Al Thanayah 1 Barsha Heights, Tecom, Dubai",
                },
            },
        }
    ),
):
    try:
        hotel = await HotelService(db).add_hotel(hotel_data)
    except ObjectAlreadyExistsException:
        raise ObjectAlreadyExistsHTTPException()

    return {"detail": "Отель успешно добавлен!", "data": hotel}


@router.put(
    "/{hotel_id}",
    summary="Обновление отеля",
    description="Полное обновление данных по отелю",
)
async def hotel_put_update(
    hotel_id: int,
    hotel_data: HotelAdd,
    db: DBDep,
):
    try:
        await HotelService(db).hotel_put_update(hotel_id, hotel_data)
    except HotelNotFoundException:
        raise HotelNotFoundHTTPException()
    except ObjectAlreadyExistsException:
        raise ObjectAlreadyExistsHTTPException()

    return {"detail": "Изменения успешно сохранены!"}


@router.patch(
    "/{hotel_id}",
    summary="Частичное обновление отеля",
    description="Обновление отеля по 'name' или 'title'",
)
async def hotel_patch_update(hotel_id: int, hotel_data: HotelPatch, db: DBDep):
    try:
        await HotelService(db).hotel_patch_update(hotel_id, hotel_data, exclude_unset=True)
    except HotelNotFoundException:
        raise HotelNotFoundHTTPException()
    except ObjectAlreadyExistsException:
        raise ObjectAlreadyExistsHTTPException()

    return {"detail": "Изменения успешно сохранены!"}


@router.delete("/{hotel_id}", summary="Удаление отеля")
async def delete_hotel(hotel_id: int, db: DBDep):
    try:
        await HotelService(db).delete_hotel(hotel_id)
    except HotelNotFoundException:
        raise HotelNotFoundHTTPException()
    except CannotDeleteHotelWithRoomsException:
        raise CannotDeleteHotelWithRoomsHTTPException()

    return {"detail": "Отель успешно удалён!"}
