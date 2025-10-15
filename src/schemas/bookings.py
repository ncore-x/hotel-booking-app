from datetime import date
from pydantic import BaseModel, ConfigDict, field_validator, model_validator
from typing import Any

from src.exceptions import (
    InvalidBookingPeriodHTTPException,
    PastDateHTTPException,
    InvalidDateRangeHTTPException,
)


class BookingAddRequest(BaseModel):
    room_id: int
    date_from: date
    date_to: date

    @field_validator("date_from", "date_to", mode="before")
    @classmethod
    def validate_date_format(cls, value: Any) -> date:
        """Проверяет и преобразует строку в дату"""
        if isinstance(value, str):
            try:
                return date.fromisoformat(value)
            except ValueError:
                raise ValueError("Неверный формат даты. Используйте YYYY-MM-DD")
        return value

    @model_validator(mode="after")
    def validate_booking_dates(self) -> "BookingAddRequest":
        today = date.today()
        if self.date_from < today:
            raise PastDateHTTPException()
        if self.date_to < today:
            raise PastDateHTTPException()
        if self.date_from >= self.date_to:
            raise InvalidDateRangeHTTPException()
        if (self.date_to - self.date_from).days < 1:
            raise InvalidBookingPeriodHTTPException()
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
