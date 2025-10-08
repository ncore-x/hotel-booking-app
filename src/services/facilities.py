from src.exceptions import FacilityTitleEmptyException, ObjectAlreadyExistsException
from src.schemas.facilities import FacilityAdd
from src.services.base import BaseService
from src.tasks.tasks import test_task


class FacilityService(BaseService):
    async def facility_add(self, data: FacilityAdd):
        if not data.title.strip():
            raise FacilityTitleEmptyException()

        existing = await self.db.facilities.get_one_or_none(title=data.title)
        if existing:
            raise ObjectAlreadyExistsException
        facility = await self.db.facilities.add(data)
        await self.db.commit()

        test_task.delay()  # type: ignore
        return facility

    async def get_facilities(self):
        return await self.db.facilities.get_all()
