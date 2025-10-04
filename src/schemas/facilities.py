from pydantic import BaseModel, ConfigDict


class FacilityAdd(BaseModel):
    title: str


class Facility(FacilityAdd):
    id: int

    model_config = ConfigDict(from_attributes=True)


class RoomFacilitiyAdd(BaseModel):
    room_id: int
    facility_id: int


class RoomFacilitiy(BaseModel):
    id: int
