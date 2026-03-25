from fastapi import APIRouter, Body, Request, Response, status
from fastapi_cache.decorator import cache

from src.exceptions import (
    FacilityTitleEmptyException,
    FacilityTitleEmptyHTTPException,
    ObjectAlreadyExistsException,
    ObjectAlreadyExistsHTTPException,
)
from src.services.facilities import FacilityService
from src.schemas.common import PaginatedResponse
from src.schemas.facilities import FacilityAdd, Facility
from src.api.dependencies import DBDep, PaginationDep, AdminDep

router = APIRouter(prefix="/facilities", tags=["Facilities"])


@router.get("", summary="Список удобств", response_model=PaginatedResponse[Facility])
@cache(expire=10)
async def get_facilities(pagination: PaginationDep, db: DBDep):
    return await FacilityService(db).get_facilities(
        page=pagination.page, per_page=pagination.per_page
    )


@router.post(
    "",
    summary="Создать удобство",
    response_model=Facility,
    status_code=status.HTTP_201_CREATED,
)
async def create_facility(
    _: AdminDep,
    db: DBDep,
    request: Request,
    response: Response,
    facility_data: FacilityAdd = Body(),
):
    try:
        facility = await FacilityService(db).facility_add(facility_data)
    except FacilityTitleEmptyException:
        raise FacilityTitleEmptyHTTPException()
    except ObjectAlreadyExistsException:
        raise ObjectAlreadyExistsHTTPException()
    response.headers["Location"] = str(request.url_for("get_facilities"))
    return facility
