import math
from datetime import date

from src.services.hotels import HotelService
from src.schemas.common import PaginatedResponse
from src.schemas.facilities import RoomFacilityAdd
from src.schemas.rooms import (
    Room,
    RoomAdd,
    RoomAddRequest,
    RoomPatch,
    RoomPatchRequest,
    RoomWithRels,
)
from src.exceptions import (
    CannotDeleteRoomWithBookingsException,
    ObjectNotFoundException,
    RoomNotFoundException,
    ObjectAlreadyExistsException,
    check_date_to_after_date_from,
)
from src.services.base import BaseService


class RoomService(BaseService):
    async def get_filtered_by_time(
        self,
        hotel_id: int,
        date_from: date,
        date_to: date,
        page: int = 1,
        per_page: int = 20,
    ) -> PaginatedResponse[RoomWithRels]:
        check_date_to_after_date_from(date_from, date_to)
        await HotelService(self.db).get_hotel_with_check(hotel_id)

        total = await self.db.rooms.count_filtered_by_time(
            hotel_id=hotel_id, date_from=date_from, date_to=date_to
        )
        items = await self.db.rooms.get_filtered_by_time(
            hotel_id=hotel_id,
            date_from=date_from,
            date_to=date_to,
            limit=per_page,
            offset=per_page * (page - 1),
        )
        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            per_page=per_page,
            pages=max(1, math.ceil(total / per_page)),
        )

    async def get_room(self, room_id: int, hotel_id: int) -> RoomWithRels:
        await HotelService(self.db).get_hotel_with_check(hotel_id)
        return await self.db.rooms.get_one_with_rels(id=room_id, hotel_id=hotel_id)

    async def create_room(self, hotel_id: int, room_data: RoomAddRequest) -> RoomWithRels:
        await HotelService(self.db).get_hotel_with_check(hotel_id)

        for f_id in room_data.facilities_ids:
            try:
                await self.db.facilities.get_one(id=f_id)
            except ObjectNotFoundException as ex:
                raise ObjectNotFoundException(
                    f"Удобство с идентификатором {f_id} не найдено!"
                ) from ex

        existing = await self.db.rooms.get_by_fields(
            hotel_id=hotel_id,
            title=room_data.title,
            description=room_data.description,
            price=room_data.price,
            quantity=room_data.quantity,
        )
        if existing:
            raise ObjectAlreadyExistsException("Номер с такими же полями уже существует!")

        _room_data = RoomAdd(hotel_id=hotel_id, **room_data.model_dump())
        room: Room = await self.db.rooms.add(_room_data)

        rooms_facilities_data = [
            RoomFacilityAdd(room_id=room.id, facility_id=f_id) for f_id in room_data.facilities_ids
        ]
        if rooms_facilities_data:
            await self.db.rooms_facilities.add_bulk(rooms_facilities_data)
        await self.db.commit()
        return await self.db.rooms.get_one_with_rels(id=room.id, hotel_id=hotel_id)

    async def room_put_update(
        self, hotel_id: int, room_id: int, room_data: RoomAddRequest
    ) -> RoomWithRels:
        await HotelService(self.db).get_hotel_with_check(hotel_id)
        await self.get_room_with_check(room_id, hotel_id)

        for f_id in room_data.facilities_ids:
            try:
                await self.db.facilities.get_one(id=f_id)
            except ObjectNotFoundException as ex:
                raise ObjectNotFoundException(
                    f"Удобство с идентификатором {f_id} не найдено!"
                ) from ex

        _room_data = RoomAdd(hotel_id=hotel_id, **room_data.model_dump())
        await self.db.rooms.edit(_room_data, id=room_id)
        await self.db.rooms_facilities.set_room_facilities(
            room_id, facilities_ids=room_data.facilities_ids
        )
        await self.db.commit()
        return await self.db.rooms.get_one_with_rels(id=room_id, hotel_id=hotel_id)

    async def room_patch_update(
        self, hotel_id: int, room_id: int, room_data: RoomPatchRequest
    ) -> RoomWithRels:
        await HotelService(self.db).get_hotel_with_check(hotel_id)
        await self.get_room_with_check(room_id, hotel_id)

        _room_data_dict = room_data.model_dump(exclude_unset=True)
        _room_data = RoomPatch(hotel_id=hotel_id, **_room_data_dict)
        await self.db.rooms.edit(_room_data, exclude_unset=True, id=room_id, hotel_id=hotel_id)

        if "facilities_ids" in _room_data_dict and _room_data_dict["facilities_ids"] is not None:
            for f_id in _room_data_dict["facilities_ids"]:
                try:
                    await self.db.facilities.get_one(id=f_id)
                except ObjectNotFoundException as ex:
                    raise ObjectNotFoundException(
                        f"Удобство с идентификатором {f_id} не найдено!"
                    ) from ex
            await self.db.rooms_facilities.set_room_facilities(
                room_id, facilities_ids=_room_data_dict["facilities_ids"]
            )
        await self.db.commit()
        return await self.db.rooms.get_one_with_rels(id=room_id, hotel_id=hotel_id)

    async def delete_room(self, hotel_id: int, room_id: int) -> None:
        await HotelService(self.db).get_hotel_with_check(hotel_id)
        await self.get_room_with_check(room_id, hotel_id)
        bookings_count = await self.db.bookings.count_by_room(room_id)
        if bookings_count > 0:
            raise CannotDeleteRoomWithBookingsException()
        await self.db.rooms.delete(id=room_id, hotel_id=hotel_id)
        await self.db.commit()

    async def get_room_with_check(self, room_id: int, hotel_id: int | None = None) -> Room:
        try:
            if hotel_id is None:
                return await self.db.rooms.get_one(id=room_id)
            return await self.db.rooms.get_one(id=room_id, hotel_id=hotel_id)
        except ObjectNotFoundException:
            raise RoomNotFoundException()
