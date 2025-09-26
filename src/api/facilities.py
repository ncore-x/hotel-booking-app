from fastapi import APIRouter, Body
from fastapi_cache.decorator import cache


from src.schemas.facilities import FacilityAdd
from src.api.dependencies import DBDep
from src.init import redis_manager
from src.tasks.tasks import test_task


router = APIRouter(
    prefix="/facilities", tags=["Удобства"])


@router.get("", summary="Получение удобств")
@cache(expire=10)
async def get_facilities(db: DBDep):
    return await db.facilities.get_all()


@router.post("", summary="Создание нового удобства")
async def create_facility(
    db: DBDep,
    facility_data: FacilityAdd = Body()
):
    facility = await db.facilities.add(facility_data)
    await db.commit()
    test_task.delay()
    return {"status": "Ok", "data": facility}
