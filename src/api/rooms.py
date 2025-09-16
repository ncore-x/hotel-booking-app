from datetime import date
from fastapi import APIRouter, Body, Query
from src.schemas.facilities import RoomFacilitiyAdd
from src.api.dependencies import DBDep
from src.schemas.rooms import RoomAdd, RoomPatch, RoomAddRequest, RoomPatchRequest

router = APIRouter(
    prefix="/hotels", tags=["Номера"])


@router.get("/{hotel_id}/rooms", summary="Получение номеров")
async def get_rooms(
        hotel_id: int,
        db: DBDep,
        date_from: date = Query(example="2025-09-01"),
        date_to: date = Query(example="2025-09-15"),
):
    return await db.rooms.get_filtered_by_time(hotel_id=hotel_id, date_from=date_from, date_to=date_to)


@router.get("/{hotel_id}/rooms/{room_id}", summary="Получение номера")
async def get_room(
    hotel_id: int,
    room_id: int,
    db: DBDep
):
    return await db.rooms.get_one_or_none(id=room_id, hotel_id=hotel_id)


@router.post("/{hotel_id}/rooms", summary="Создание нового номера")
async def create_room(
        hotel_id: int,
        db: DBDep,
        room_data: RoomAddRequest = Body()):
    _room_data = RoomAdd(hotel_id=hotel_id, **room_data.model_dump())
    room = await db.rooms.add(_room_data)
    rooms_facilities_data = [RoomFacilitiyAdd(
        room_id=room.id, facility_id=f_id) for f_id in room_data.facilities_ids]
    await db.rooms_facilities.add_bulk(rooms_facilities_data)
    await db.commit()
    return {"status": "Ok", "data": room}


@router.put("/{hotel_id}/rooms/{room_id}", summary="Обновление номера", description="Полное обновление данных по номеру")
async def room_put_update(
    hotel_id: int,
    room_id: int,
    room_data: RoomAddRequest,
    db: DBDep
):
    _room_data = RoomAdd(hotel_id=hotel_id, **room_data.model_dump())
    await db.rooms.edit(_room_data, id=room_id)
    await db.commit()
    return {"status": "Ok"}


@router.patch("/{hotel_id}/rooms/{room_id}", summary="Частичное обновление отеля")
async def room_patch_update(
    hotel_id: int,
    room_id: int,
    room_data: RoomPatchRequest,
    db: DBDep
):
    _room_data = RoomPatch(
        hotel_id=hotel_id, **room_data.model_dump(exclude_unset=True))
    await db.rooms.edit(_room_data, exclude_unset=True, id=room_id, hotel_id=hotel_id)
    await db.commit()
    return {"status": "Ok"}


@router.delete("/{hotel_id}/rooms/{room_id}", summary="Удаление номера")
async def delete_room(
    hotel_id: int,
    room_id: int,
    db: DBDep
):
    await db.rooms.delete(id=room_id, hotel_id=hotel_id)
    await db.commit()
    return {"status": "OK"}
