from fastapi import APIRouter, Body
from fastapi_cache.decorator import cache

from src.exceptions import (
    FacilityTitleEmptyException,
    FacilityTitleEmptyHTTPException,
    ObjectAlreadyExistsException,
    ObjectAlreadyExistsHTTPException,
)
from src.services.facilities import FacilityService
from src.schemas.facilities import FacilityAdd
from src.api.dependencies import DBDep


router = APIRouter(prefix="/facilities", tags=["Удобства"])


@router.get("", summary="Получение удобств")
@cache(expire=10)
async def get_facilities(db: DBDep):
    return await FacilityService(db).get_facilities()


@router.post("", summary="Создание нового удобства")
async def create_facility(db: DBDep, facility_data: FacilityAdd = Body()):
    try:
        facility = await FacilityService(db).facility_add(facility_data)
    except FacilityTitleEmptyException:
        raise FacilityTitleEmptyHTTPException
    except ObjectAlreadyExistsException:
        raise ObjectAlreadyExistsHTTPException
    return {"detail": "Удобство добавлено!", "data": facility}
