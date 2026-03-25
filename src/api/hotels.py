from datetime import date
from typing import Literal

from fastapi import Query, APIRouter, Body, Request, Response, status
from fastapi_cache.decorator import cache

from src.services.hotels import HotelService
from src.exceptions import (
    CannotDeleteHotelWithRoomsException,
    CannotDeleteHotelWithRoomsHTTPException,
    HotelNotFoundException,
    HotelNotFoundHTTPException,
    InvalidDateRangeException,
    InvalidDateRangeHTTPException,
    ObjectNotFoundException,
    ObjectAlreadyExistsException,
    ObjectAlreadyExistsHTTPException,
)
from src.api.dependencies import PaginationDep, DBDep, AdminDep
from src.schemas.common import PaginatedResponse
from src.schemas.hotels import HotelPatch, HotelAdd, Hotel

router = APIRouter(prefix="/hotels", tags=["Hotels"])


@router.get("", summary="Список доступных отелей", response_model=PaginatedResponse[Hotel])
@cache(expire=10)
async def get_hotels(
    pagination: PaginationDep,
    db: DBDep,
    location: str | None = Query(None, description="Локация"),
    title: str | None = Query(None, description="Название отеля"),
    date_from: date = Query(examples=["2025-09-01"]),
    date_to: date = Query(examples=["2025-09-15"]),
    sort_by: Literal["id", "title", "location"] = Query("id", description="Поле сортировки"),
    order: Literal["asc", "desc"] = Query("asc", description="Направление сортировки"),
):
    try:
        return await HotelService(db).get_filtered_by_time(
            pagination, location, title, date_from, date_to, sort_by, order,
        )
    except InvalidDateRangeException:
        raise InvalidDateRangeHTTPException()


@router.get("/{hotel_id}", summary="Получить отель", response_model=Hotel)
@cache(expire=10)
async def get_hotel(hotel_id: int, db: DBDep):
    try:
        return await HotelService(db).get_hotel(hotel_id)
    except ObjectNotFoundException:
        raise HotelNotFoundHTTPException()


@router.post(
    "",
    summary="Создать отель",
    response_model=Hotel,
    status_code=status.HTTP_201_CREATED,
)
async def create_hotel(
    _: AdminDep,
    request: Request,
    response: Response,
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
    response.headers["Location"] = str(request.url_for("get_hotel", hotel_id=hotel.id))
    return hotel


@router.put("/{hotel_id}", summary="Полное обновление отеля", response_model=Hotel)
async def hotel_put_update(_: AdminDep, hotel_id: int, hotel_data: HotelAdd, db: DBDep):
    try:
        return await HotelService(db).hotel_put_update(hotel_id, hotel_data)
    except HotelNotFoundException:
        raise HotelNotFoundHTTPException()
    except ObjectAlreadyExistsException:
        raise ObjectAlreadyExistsHTTPException()


@router.patch("/{hotel_id}", summary="Частичное обновление отеля", response_model=Hotel)
async def hotel_patch_update(_: AdminDep, hotel_id: int, hotel_data: HotelPatch, db: DBDep):
    try:
        return await HotelService(db).hotel_patch_update(hotel_id, hotel_data, exclude_unset=True)
    except HotelNotFoundException:
        raise HotelNotFoundHTTPException()
    except ObjectAlreadyExistsException:
        raise ObjectAlreadyExistsHTTPException()


@router.delete(
    "/{hotel_id}",
    summary="Удалить отель",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_hotel(_: AdminDep, hotel_id: int, db: DBDep):
    try:
        await HotelService(db).delete_hotel(hotel_id)
    except HotelNotFoundException:
        raise HotelNotFoundHTTPException()
    except CannotDeleteHotelWithRoomsException:
        raise CannotDeleteHotelWithRoomsHTTPException()
