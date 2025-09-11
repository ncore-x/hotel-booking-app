from fastapi import APIRouter, Body
from src.repositories.rooms import RoomsRepository
from src.database import async_session_maker
from src.schemas.rooms import RoomAdd, RoomPatch, RoomAddRequest, RoomPatchRequest

router = APIRouter(
    prefix="/hotels", tags=["Номера"])


@router.get("/{hotel_id}/rooms", summary="Получение номеров", description="Можно фильтровать по title или location")
async def get_rooms(
    hotel_id: int
):
    async with async_session_maker() as session:
        return await RoomsRepository(session).get_filtered(hotel_id=hotel_id)


@router.get("/{hotel_id}/rooms/{room_id}", summary="Получение номера")
async def get_room(hotel_id: int, room_id: int):
    async with async_session_maker() as session:
        return await RoomsRepository(session).get_one_or_none(id=room_id, hotel_id=hotel_id)


@router.post("/{hotel_id}/rooms", summary="Создание нового номера")
async def create_room(hotel_id: int, room_data: RoomAddRequest = Body()):
    _room_data = RoomAdd(hotel_id=hotel_id, **room_data.model_dump())
    async with async_session_maker() as session:
        room = await RoomsRepository(session).add(_room_data)
        await session.commit()
    return {"status": "Ok", "data": room}


@router.put("/{hotel_id}/rooms/{room_id}", summary="Обновление номера", description="Полное обновление данных по номеру")
async def room_put_update(hotel_id: int, room_id: int, room_data: RoomAddRequest):
    _room_data = RoomAdd(hotel_id=hotel_id, **room_data.model_dump())
    async with async_session_maker() as session:
        await RoomsRepository(session).edit(_room_data, id=room_id)
        await session.commit()
    return {"status": "Ok"}


@router.patch("/{hotel_id}/rooms/{room_id}", summary="Частичное обновление отеля")
async def room_patch_update(
    hotel_id: int,
    room_id: int,
    room_data: RoomPatchRequest
):
    _room_data = RoomPatch(
        hotel_id=hotel_id, **room_data.model_dump(exclude_unset=True))
    async with async_session_maker() as session:
        await RoomsRepository(session).edit(_room_data, exclude_unset=True, id=room_id, hotel_id=hotel_id)
        await session.commit()
    return {"status": "Ok"}


@router.delete("/{hotel_id}/rooms/{room_id}", summary="Удаление номера")
async def delete_room(hotel_id: int, room_id: int):
    async with async_session_maker() as session:
        await RoomsRepository(session).delete(id=room_id, hotel_id=hotel_id)
        await session.commit()
    return {"status": "OK"}
