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


class TestUserSchema:
    def test_user_has_password_defaults_false(self):
        from src.schemas.users import User

        u = User(id=1, email="a@b.com")
        assert u.has_password is False

    def test_user_with_hashed_password_set(self):
        from src.schemas.users import UserWithHashedPassword

        u = UserWithHashedPassword(id=1, email="a@b.com", hashed_password="bcrypthash")
        assert u.has_password is True

    def test_user_with_hashed_password_none(self):
        from src.schemas.users import UserWithHashedPassword

        u = UserWithHashedPassword(id=1, email="a@b.com", hashed_password=None)
        assert u.has_password is False

    def test_user_fields_do_not_include_hashed_password(self):
        from src.schemas.users import User

        assert "hashed_password" not in User.model_fields

    def test_has_password_from_orm_attributes(self):
        from unittest.mock import MagicMock
        from src.schemas.users import UserWithHashedPassword

        orm = MagicMock()
        orm.id = 1
        orm.email = "a@b.com"
        orm.hashed_password = "somehash"
        orm.is_admin = False
        orm.first_name = orm.last_name = orm.phone = orm.birth_date = None
        orm.gender = orm.citizenship = orm.avatar_filename = None
        orm.oauth_provider = orm.oauth_avatar_url = None

        u = UserWithHashedPassword.model_validate(orm, from_attributes=True)
        assert u.has_password is True
