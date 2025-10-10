from typing import Optional, Annotated
from pydantic import BaseModel, Field, field_validator

NonEmptyStr = Annotated[str, Field(strip_whitespace=True)]


def not_blank(value: str) -> str:
    if not (value and value.strip()):
        raise ValueError("Поле не может быть пустым")
    return value


class HotelAdd(BaseModel):
    title: NonEmptyStr
    location: NonEmptyStr

    @field_validator("title", "location")
    @classmethod
    def validate_not_blank(cls, value: str) -> str:
        return not_blank(value)


class HotelPatch(BaseModel):
    title: Optional[str] = None
    location: Optional[str] = None

    @field_validator("title", "location")
    @classmethod
    def validate_not_blank_optional(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        return not_blank(value)


class Hotel(HotelAdd):
    id: int
