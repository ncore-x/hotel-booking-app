import pytest
from datetime import date, timedelta

from src.schemas.bookings import BookingAddRequest


def future(days: int) -> str:
    return (date.today() + timedelta(days=days)).isoformat()


class TestBookingAddRequest:
    def test_valid(self):
        b = BookingAddRequest(room_id=1, date_from=future(5), date_to=future(10))
        assert b.room_id == 1

    def test_date_from_in_past_raises(self):
        with pytest.raises(ValueError, match="прошлом"):
            BookingAddRequest(room_id=1, date_from="2020-01-01", date_to=future(5))

    def test_date_to_in_past_raises(self):
        with pytest.raises(ValueError, match="прошлом"):
            BookingAddRequest(room_id=1, date_from=future(1), date_to="2020-01-01")

    def test_date_from_equals_date_to_raises(self):
        d = future(5)
        with pytest.raises(ValueError, match="позже"):
            BookingAddRequest(room_id=1, date_from=d, date_to=d)

    def test_date_from_after_date_to_raises(self):
        with pytest.raises(ValueError, match="позже"):
            BookingAddRequest(room_id=1, date_from=future(10), date_to=future(5))

    def test_invalid_date_format_raises(self):
        with pytest.raises(ValueError, match="формат"):
            BookingAddRequest(room_id=1, date_from="not-a-date", date_to=future(5))

    def test_date_parsed_from_string(self):
        b = BookingAddRequest(room_id=1, date_from=future(3), date_to=future(7))
        assert isinstance(b.date_from, date)
        assert isinstance(b.date_to, date)
