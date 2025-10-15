from pydantic import BaseModel, ConfigDict, field_validator, model_validator
from typing import List, Optional

from src.schemas.facilities import Facility


class RoomAddRequest(BaseModel):
    title: str
    description: Optional[str] = None
    price: int
    quantity: int
    facilities_ids: List[int] = []

    @model_validator(mode="after")
    def validate_required_fields(self):
        errors = []

        if self.title is None or not str(self.title).strip():
            errors.append("Поле 'title' обязательно для заполнения!")

        if self.price is None:
            errors.append("Поле 'price' обязательно для заполнения!")
        elif self.price <= 0:
            errors.append("Цена должна быть положительной!")

        if self.quantity is None:
            errors.append("Поле 'quantity' обязательно для заполнения!")
        elif self.quantity < 0:
            errors.append("Количество должно быть больше или равно 0")

        if errors:
            raise ValueError("; ".join(errors))

        return self

    @field_validator("title", mode="before")
    @classmethod
    def title_not_empty(cls, value):
        if value is not None:
            return str(value).strip()
        return value

    @field_validator("facilities_ids", mode="before")
    @classmethod
    def facilities_ids_valid(cls, value):
        if value is None:
            return []
        if any((not isinstance(i, int) or i <= 0) for i in value):
            raise ValueError("facilities_ids должен содержать только положительные целые числа!")
        return list(dict.fromkeys(value))


class RoomPatchRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    price: int | None = None
    quantity: int | None = None
    facilities_ids: list[int] | None = None

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not value.strip():
            raise ValueError("Название не может быть пустым!")
        return value.strip()

    @field_validator("price")
    @classmethod
    def price_positive(cls, value: int | None) -> int | None:
        if value is None:
            return None
        if value <= 0:
            raise ValueError("Цена должна быть положительной!")
        return value

    @field_validator("quantity")
    @classmethod
    def quantity_non_negative(cls, value: int | None) -> int | None:
        if value is None:
            return None
        if value < 0:
            raise ValueError("Количество должно быть больше или равно 0!")
        return value

    @field_validator("facilities_ids")
    @classmethod
    def facilities_ids_valid(cls, value: list[int] | None) -> list[int] | None:
        if value is None:
            return None
        if any((not isinstance(i, int) or i <= 0) for i in value):
            raise ValueError("facilities_ids должен содержать только положительные целые числа!")
        return list(dict.fromkeys(value))


class RoomAdd(BaseModel):
    hotel_id: int
    title: str
    description: str | None = None
    price: int
    quantity: int


class Room(RoomAdd):
    id: int
    model_config = ConfigDict(from_attributes=True)


class RoomWithRels(Room):
    facilities: list[Facility]


class RoomPatch(BaseModel):
    hotel_id: int | None = None
    title: str | None = None
    description: str | None = None
    price: int | None = None
    quantity: int | None = None
