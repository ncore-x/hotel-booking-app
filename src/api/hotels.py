from fastapi import Query, APIRouter, Body

from sqlalchemy import insert, select, func

from repositories.hotels import HotelsRepository
from src.database import async_session_maker
from models.hotels import HotelsOrm
from src.api.dependencies import PaginationDep
from src.schemas.hotels import Hotel, HotelPatch

router = APIRouter(prefix="/hotels", tags=["Отели"])


@router.get("", summary="Получение отеля(ей)", description="Можно фильтровать по id или title")
async def get_hotels(
    pagination: PaginationDep,
    location: str | None = Query(None, description="Локация"),
    title: str | None = Query(None, description="Название отеля"),
):
    async with async_session_maker() as session:
        return await HotelsRepository(session).get_all()

    # per_page = pagination.per_page or 5
        # query = select(HotelsOrm)
        # if location:
        #     query = query.filter(func.lower(
        #         HotelsOrm.location).contains(location.strip().lower()))
        # if title:
        #     query = query.filter(func.lower(
        #         HotelsOrm.title).contains(title.strip().lower()))
        # query = (
        #     query
        #     .limit(per_page)
        #     .offset(per_page * (pagination.page - 1))
        # )
        # result = await session.execute(query)

        # hotels = result.scalars().all()
        # return hotels


@router.post("", summary="Создание нового отеля")
async def create_hotel(hotel_data: Hotel = Body(openapi_examples={
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
        add_hotel_stmt = insert(HotelsOrm).values(**hotel_data.model_dump())
        # add_hotel_stmt.compile(compile_kwargs={"literal_binds": True})
        await session.execute(add_hotel_stmt)
        await session.commit()
    return {"status": "Ok"}


@router.put("/{hotel_id}", summary="Обновление отеля", description="Полное обноелвение данных по отелю")
def hotel_put_update(hotel_id: int, hotel_data: Hotel):
    global hotels
    hotel = [hotel for hotel in hotels if hotel["id"] == hotel_id][0]
    hotel["title"] = hotel_data.title
    hotel["name"] = hotel_data.name
    return {"status": "Ok"}


@router.patch("/{hotel_id}", summary="Частичное обновление отеля", description="Обновление отеля по 'name' или 'title'")
def hotel_patch_update(hotel_id: int, hotel_data: HotelPatch):
    global hotels
    hotel = [hotel for hotel in hotels if hotel["id"] == hotel_id][0]
    if hotel["id"] == hotel_id:
        if hotel_data.title:
            hotel["title"] = hotel_data.title
        if hotel_data.name:
            hotel["name"] = hotel_data.name
        return {"status": "Ok"}


@router.delete("/{hotel_id}")
def delete_hotel(hotel_id: int):
    global hotels
    hotels = [hotel for hotel in hotels if hotel["id"] != hotel_id]
    return {"status": "OK"}
