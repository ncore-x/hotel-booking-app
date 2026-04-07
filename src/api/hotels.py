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
from src.middleware.prometheus import SEARCH_REQUESTS
from src.schemas.common import PaginatedResponse
from src.schemas.hotels import HotelPatch, HotelAdd, Hotel, AutocompleteResult

router = APIRouter(prefix="/hotels", tags=["Hotels"])


@router.get("", summary="Список доступных отелей", response_model=PaginatedResponse[Hotel])
@cache(expire=10)
async def get_hotels(
    pagination: PaginationDep,
    db: DBDep,
    city: str | None = Query(None, description="Город"),
    title: str | None = Query(None, description="Название отеля"),
    search: str | None = Query(None, description="Поиск по городу, названию и адресу"),
    date_from: date | None = Query(None, examples=["2025-09-01"]),
    date_to: date | None = Query(None, examples=["2025-09-15"]),
    sort_by: Literal["id", "title", "city"] = Query("id", description="Поле сортировки"),
    order: Literal["asc", "desc"] = Query("asc", description="Направление сортировки"),
    guests: int = Query(1, ge=1, le=20, description="Количество гостей"),
):
    SEARCH_REQUESTS.labels(app_name="hotel_booking").inc()
    try:
        return await HotelService(db).get_filtered_by_time(
            pagination,
            city,
            title,
            date_from,
            date_to,
            sort_by,
            order,
            guests,
            search,
        )
    except InvalidDateRangeException:
        raise InvalidDateRangeHTTPException()


@router.get("/popular-locations", summary="Популярные локации", response_model=list[str])
@cache(expire=300)
async def popular_locations(db: DBDep):
    return await HotelService(db).popular_locations()


@router.get("/autocomplete", summary="Подсказки для поиска", response_model=AutocompleteResult)
@cache(expire=30)
async def autocomplete_hotels(
    db: DBDep,
    q: str = Query(..., min_length=1, max_length=100),
):
    return await HotelService(db).autocomplete_combined(q.strip())


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
