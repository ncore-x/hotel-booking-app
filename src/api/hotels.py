from fastapi import Query, APIRouter, Body

from src.repositories.hotels import HotelsRepository
from src.database import async_session_maker
from src.api.dependencies import PaginationDep
from src.schemas.hotels import HotelAdd, HotelPatch

router = APIRouter(prefix="/hotels", tags=["Отели"])


@router.get("", summary="Получение отелей", description="Можно фильтровать по title или location")
async def get_hotels(
    pagination: PaginationDep,
    location: str | None = Query(None, description="Локация"),
    title: str | None = Query(None, description="Название отеля"),
):
    per_page = pagination.per_page or 5
    async with async_session_maker() as session:
        return await HotelsRepository(session).get_all(
            location=location,
            title=title,
            limit=per_page,
            offset=per_page * (pagination.page - 1)
        )


@router.get("/{hotel_id}", summary="Получение отеля")
async def get_hotel(hotel_id: int):
    async with async_session_maker() as session:
        return await HotelsRepository(session).get_one_or_none(id=hotel_id)


@router.post("", summary="Создание нового отеля")
async def create_hotel(hotel_data: HotelAdd = Body(openapi_examples={
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
    async with async_session_maker() as session:
        hotel = await HotelsRepository(session).add(hotel_data)
        await session.commit()
    return {"status": "Ok", "data": hotel}


@router.put("/{hotel_id}", summary="Обновление отеля", description="Полное обновление данных по отелю")
async def hotel_put_update(hotel_id: int, hotel_data: HotelAdd):
    async with async_session_maker() as session:
        await HotelsRepository(session).edit(hotel_data, id=hotel_id)
        await session.commit()
    return {"status": "Ok"}


@router.patch("/{hotel_id}", summary="Частичное обновление отеля", description="Обновление отеля по 'name' или 'title'")
async def hotel_patch_update(hotel_id: int, hotel_data: HotelPatch):
    async with async_session_maker() as session:
        await HotelsRepository(session).edit(hotel_data, exclude_unset=True, id=hotel_id)
        await session.commit()
    return {"status": "Ok"}


@router.delete("/{hotel_id}", summary="Удаление отеля")
async def delete_hotel(hotel_id: int):
    async with async_session_maker() as session:
        await HotelsRepository(session).delete(id=hotel_id)
        await session.commit()
    return {"status": "OK"}
