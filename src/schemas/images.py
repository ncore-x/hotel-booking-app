from datetime import datetime

from pydantic import BaseModel, ConfigDict


class HotelImageAdd(BaseModel):
    hotel_id: int
    filename: str
    content_type: str


class HotelImage(HotelImageAdd):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ImageUploadResponse(BaseModel):
    id: int
    hotel_id: int
    filename: str
    content_type: str
    size: int
    width: int
    height: int
