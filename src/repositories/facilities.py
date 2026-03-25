from sqlalchemy import insert, select, delete, func
from typing import Sequence

from src.repositories.mappers.mappers import FacilityDataMapper
from src.models.facilities import FacilitiesOrm, RoomsFacilitiesOrm
from src.repositories.base import BaseRepository


class FacilitiesRepository(BaseRepository):
    model = FacilitiesOrm
    mapper = FacilityDataMapper

    async def count(self) -> int:
        result = await self.session.execute(
            select(func.count()).select_from(self.model)
        )
        return result.scalar_one()

    async def get_paginated(self, limit: int, offset: int):
        query = select(self.model).order_by(self.model.id).limit(limit).offset(offset)
        result = await self.session.execute(query)
        return [self.mapper.map_to_domain_entity(m) for m in result.scalars().all()]


class RoomsFacilitiesRepository(BaseRepository):
    model: type[RoomsFacilitiesOrm] = RoomsFacilitiesOrm
    mapper = None  # type: ignore  # M2M таблица не требует маппинга доменных объектов

    async def set_room_facilities(
        self, room_id: int, facilities_ids: list[int]
    ) -> None:
        get_current_facilities_ids_query = select(self.model.facility_id).filter_by(
            room_id=room_id
        )
        res = await self.session.execute(get_current_facilities_ids_query)
        current_facilities_ids: Sequence[int] = res.scalars().all()
        ids_to_delete: list[int] = list(
            set(current_facilities_ids) - set(facilities_ids)
        )
        ids_to_insert: list[int] = list(
            set(facilities_ids) - set(current_facilities_ids)
        )

        if ids_to_delete:
            delete_m2m_facilities_stmt = delete(self.model).filter(
                self.model.room_id == room_id,
                self.model.facility_id.in_(ids_to_delete),
            )
            await self.session.execute(delete_m2m_facilities_stmt)

        if ids_to_insert:
            insert_m2m_facilities_stmt = insert(self.model).values(
                [{"room_id": room_id, "facility_id": f_id} for f_id in ids_to_insert]
            )
            await self.session.execute(insert_m2m_facilities_stmt)
