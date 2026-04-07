import math

from src.exceptions import FacilityTitleEmptyException, ObjectAlreadyExistsException, ObjectNotFoundException
from src.schemas.common import PaginatedResponse
from src.schemas.facilities import FacilityAdd, Facility
from src.services.base import BaseService


class FacilityService(BaseService):
    async def facility_add(self, data: FacilityAdd) -> Facility:
        if not data.title.strip():
            raise FacilityTitleEmptyException()

        try:
            facility = await self.db.facilities.add(data)
            await self.db.commit()
        except ObjectAlreadyExistsException:
            raise
        return facility

    async def facility_delete(self, facility_id: int) -> None:
        await self.db.facilities.get_one(id=facility_id)  # raises ObjectNotFoundException if missing
        await self.db.facilities.delete(id=facility_id)
        await self.db.commit()

    async def get_facilities(
        self, page: int = 1, per_page: int = 50
    ) -> PaginatedResponse[Facility]:
        total = await self.db.facilities.count()
        items = await self.db.facilities.get_paginated(limit=per_page, offset=per_page * (page - 1))
        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            per_page=per_page,
            pages=max(1, math.ceil(total / per_page)),
        )
