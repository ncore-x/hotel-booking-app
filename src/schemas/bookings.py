from datetime import date, datetime, timezone
from pydantic import BaseModel, ConfigDict, field_validator, model_validator
from typing import Any


class BookingAddRequest(BaseModel):
    room_id: int
    date_from: date
    date_to: date

    @field_validator("date_from", "date_to", mode="before")
    @classmethod
    def validate_date_format(cls, value: Any) -> date:
        if isinstance(value, str):
            try:
                return date.fromisoformat(value)
            except ValueError:
                raise ValueError("Неверный формат даты. Используйте YYYY-MM-DD")
        return value

    @model_validator(mode="after")
    def validate_booking_dates(self) -> "BookingAddRequest":
        today = datetime.now(tz=timezone.utc).date()
        if self.date_from < today:
            raise ValueError("Дата не может быть в прошлом!")
        if self.date_to < today:
            raise ValueError("Дата не может быть в прошлом!")
        if self.date_from >= self.date_to:
            raise ValueError("Дата заезда не может быть позже даты выезда!")
        return self


class BookingPatchRequest(BaseModel):
    date_from: date | None = None
    date_to: date | None = None

    @model_validator(mode="after")
    def validate_booking_dates(self) -> "BookingPatchRequest":
        today = datetime.now(tz=timezone.utc).date()
        if self.date_from is not None and self.date_from < today:
            raise ValueError("Дата не может быть в прошлом!")
        if self.date_to is not None and self.date_to < today:
            raise ValueError("Дата не может быть в прошлом!")
        if self.date_from is not None and self.date_to is not None:
            if self.date_from >= self.date_to:
                raise ValueError("Дата заезда не может быть позже даты выезда!")
        return self


class BookingAdd(BaseModel):
    user_id: int
    room_id: int
    date_from: date
    date_to: date
    price: int


class Booking(BookingAdd):
    id: int

    model_config = ConfigDict(from_attributes=True)
