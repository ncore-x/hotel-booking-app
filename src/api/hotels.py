from datetime import date

from fastapi import Query, APIRouter, Body

from src.api.dependencies import PaginationDep, DBDep
from src.schemas.hotels import HotelPatch, HotelAdd

router = APIRouter(prefix="/hotels", tags=["Отели"])


@router.get("", summary="Получение отелей")
async def get_hotels(
        pagination: PaginationDep,
        db: DBDep,
        location: str | None = Query(None, description="Локация"),
        title: str | None = Query(None, description="Название отеля"),
        date_from: date = Query(example="2025-09-01"),
        date_to: date = Query(example="2025-09-15"),
):
    per_page = pagination.per_page or 5

    return await db.hotels.get_filtered_by_time(
        date_from=date_from,
        date_to=date_to,
        location=location,
        title=title,
        limit=per_page,
        offset=per_page * (pagination.page - 1)
    )


@router.get("/{hotel_id}", summary="Получение отеля")
async def get_hotel(
        hotel_id: int,
        db: DBDep):
    return await db.hotels.get_one_or_none(id=hotel_id)


@router.post("", summary="Создание нового отеля")
async def create_hotel(
    db: DBDep,
    hotel_data: HotelAdd = Body(openapi_examples={
        "1": {"summary": "Сочи", "value": {
        "title": "Апартаменты Brevis Rents",
        "location": "Сочи, ул. Орджоникидзе, д. 11/1"
        }},
        "2": {"summary": "Дубай", "value": {
        "title": "Signature 1 Hotel Tecom",
        "location": "Al Thanayah 1 Barsha Heights, Tecom, Дубай",
        }}
    })
):
    hotel = await db.hotels.add(hotel_data)
    await db.commit()
    return {"status": "Ok", "data": hotel}


@router.put("/{hotel_id}", summary="Обновление отеля", description="Полное обновление данных по отелю")
async def hotel_put_update(
    hotel_id: int,
    hotel_data: HotelAdd,
    db: DBDep,
):
    await db.hotels.edit(hotel_data, id=hotel_id)
    await db.commit()
    return {"status": "Ok"}


@router.patch("/{hotel_id}", summary="Частичное обновление отеля", description="Обновление отеля по 'name' или 'title'")
async def hotel_patch_update(
    hotel_id: int,
    hotel_data: HotelPatch,
    db: DBDep
):
    await db.hotels.edit(hotel_data, exclude_unset=True, id=hotel_id)
    await db.commit()
    return {"status": "Ok"}


@router.delete("/{hotel_id}", summary="Удаление отеля")
async def delete_hotel(
    hotel_id: int,
    db: DBDep
):
    await db.hotels.delete(id=hotel_id)
    await db.commit()
    return {"status": "OK"}
