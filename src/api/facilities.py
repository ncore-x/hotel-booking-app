import json
from fastapi import APIRouter, Body

from src.schemas.facilities import FacilityAdd
from src.api.dependencies import DBDep
from src.init import redis_manager

router = APIRouter(
    prefix="/facilities", tags=["Удобства"])


@router.get("", summary="Получение удобств")
async def get_facilities(db: DBDep):
    facilities_from_cache = await redis_manager.get("facilities")
    print(f"{facilities_from_cache=}")
    if not facilities_from_cache:
        facilities = await db.facilities.get_all()
        facilities_schemas = [f.model_dump() for f in facilities]
        facilities_json = json.dumps(facilities_schemas)
        await redis_manager.set("facilities", facilities_json, 10)

        return facilities
    else:
        facilities_dicts = json.loads(facilities_from_cache)
        return facilities_dicts


@router.post("", summary="Создание нового удобства")
async def create_facility(
    db: DBDep,
    facility_data: FacilityAdd = Body()

):
    facility = await db.facilities.add(facility_data)
    await db.commit()
    return {"status": "Ok", "data": facility}
