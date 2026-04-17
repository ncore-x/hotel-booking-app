from typing import Optional, Annotated
from pydantic import BaseModel, StringConstraints, field_validator

NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True)]


def not_blank(value: str) -> str:
    if not (value and value.strip()):
        raise ValueError("Поле не может быть пустым")
    return value


class HotelAdd(BaseModel):
    title: NonEmptyStr
    city: NonEmptyStr
    address: Optional[str] = None

    @field_validator("title", "city")
    @classmethod
    def validate_not_blank(cls, value: str) -> str:
        return not_blank(value)


class HotelPatch(BaseModel):
    title: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None

    @field_validator("title", "city")
    @classmethod
    def validate_not_blank_optional(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        return not_blank(value)


class Hotel(HotelAdd):
    id: int
    cover_image_url: str | None = None


class HotelSuggestion(BaseModel):
    title: str
    city: str
    address: str | None = None


class AutocompleteResult(BaseModel):
    locations: list[str]
    hotels: list[HotelSuggestion]
