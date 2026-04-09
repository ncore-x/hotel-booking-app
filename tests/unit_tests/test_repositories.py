"""Unit tests for repository layer.

Strategy: mock AsyncSession.execute() to return controlled results.
This tests the mapping logic, exception translation, and query branching
without requiring a real database.
"""

from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ─── Helpers ──────────────────────────────────────────────────────────────────


def _make_session():
    """Return a mock AsyncSession with execute returning an AsyncMock."""
    session = AsyncMock()
    return session


def _scalar_result(value):
    """Simulate result.scalar_one() / scalar_one_or_none()."""
    result = MagicMock()
    result.scalar_one.return_value = value
    result.scalar_one_or_none.return_value = value
    return result


def _scalars_result(items):
    """Simulate result.scalars().all() / one() / one_or_none()."""
    result = MagicMock()
    scalars = MagicMock()
    scalars.all.return_value = items
    scalars.one.return_value = items[0] if items else None
    scalars.one_or_none.return_value = items[0] if items else None
    scalars.first.return_value = items[0] if items else None
    result.scalars.return_value = scalars
    return result


def _make_orm_hotel(id=1, title="Test Hotel", city="Moscow", address="Addr"):
    m = MagicMock()
    m.id = id
    m.title = title
    m.city = city
    m.address = address
    m.cover_image_url = None
    return m


def _make_orm_room(id=1, hotel_id=1, title="Room", description="Desc", price=1000, quantity=2):
    m = MagicMock()
    m.id = id
    m.hotel_id = hotel_id
    m.title = title
    m.description = description
    m.price = price
    m.quantity = quantity
    m.facilities = []
    return m


def _make_orm_booking(id=1, user_id=1, room_id=1, date_from=None, date_to=None, price=1000):
    m = MagicMock()
    m.id = id
    m.user_id = user_id
    m.room_id = room_id
    m.date_from = date_from or date(2026, 5, 1)
    m.date_to = date_to or date(2026, 5, 5)
    m.price = price
    return m


def _make_orm_user(id=1, email="user@test.com", hashed_password="hash", is_admin=False):
    m = MagicMock()
    m.id = id
    m.email = email
    m.hashed_password = hashed_password
    m.is_admin = is_admin
    return m


# ─── BaseRepository ───────────────────────────────────────────────────────────


class TestBaseRepository:
    def _make_repo(self, session=None):
        from src.repositories.hotels import HotelsRepository

        return HotelsRepository(session=session or _make_session())

    async def test_get_one_not_found_raises(self):
        from sqlalchemy.exc import NoResultFound

        from src.exceptions import ObjectNotFoundException

        session = _make_session()
        result = MagicMock()
        result.scalar_one.side_effect = NoResultFound()
        session.execute.return_value = result

        repo = self._make_repo(session)
        with pytest.raises(ObjectNotFoundException):
            await repo.get_one(id=999)

    async def test_get_one_or_none_returns_none(self):
        session = _make_session()
        result = MagicMock()
        scalars = MagicMock()
        scalars.one_or_none.return_value = None
        result.scalars.return_value = scalars
        session.execute.return_value = result

        repo = self._make_repo(session)
        assert await repo.get_one_or_none(id=999) is None

    async def test_add_unique_violation_raises(self):
        from asyncpg import UniqueViolationError
        from sqlalchemy.exc import IntegrityError

        from src.exceptions import ObjectAlreadyExistsException
        from src.schemas.hotels import HotelAdd

        session = _make_session()
        cause = UniqueViolationError()
        exc = IntegrityError("stmt", {}, cause)
        exc.orig = MagicMock(__cause__=cause)
        session.execute.side_effect = exc

        repo = self._make_repo(session)
        with pytest.raises(ObjectAlreadyExistsException):
            await repo.add(HotelAdd(title="H", city="C"))

    async def test_get_filtered_returns_list(self):
        session = _make_session()
        orm_hotel = _make_orm_hotel()
        session.execute.return_value = _scalars_result([orm_hotel])

        repo = self._make_repo(session)
        with patch.object(
            type(repo).mapper, "map_to_domain_entity", return_value=MagicMock()
        ) as mock_map:
            result = await repo.get_filtered()
        assert len(result) == 1
        mock_map.assert_called_once_with(orm_hotel)


# ─── UsersRepository ──────────────────────────────────────────────────────────


class TestUsersRepository:
    def _make_repo(self, session=None):
        from src.repositories.users import UsersRepository

        return UsersRepository(session=session or _make_session())

    async def test_get_user_with_hashed_password_success(self):
        session = _make_session()
        orm_user = _make_orm_user()
        session.execute.return_value = _scalars_result([orm_user])

        repo = self._make_repo(session)
        result = await repo.get_user_with_hashed_password("user@test.com")
        assert result.email == "user@test.com"
        assert result.hashed_password == "hash"

    async def test_get_user_with_hashed_password_not_found(self):
        from sqlalchemy.exc import NoResultFound

        from src.exceptions import ObjectNotFoundException

        session = _make_session()
        result_mock = MagicMock()
        scalars = MagicMock()
        scalars.one.side_effect = NoResultFound()
        result_mock.scalars.return_value = scalars
        session.execute.return_value = result_mock

        repo = self._make_repo(session)
        with pytest.raises(ObjectNotFoundException):
            await repo.get_user_with_hashed_password("ghost@test.com")

    async def test_get_user_by_id_success(self):
        session = _make_session()
        orm_user = _make_orm_user(id=42)
        session.execute.return_value = _scalars_result([orm_user])

        repo = self._make_repo(session)
        result = await repo.get_user_with_hashed_password_by_id(42)
        assert result.email == "user@test.com"

    async def test_get_user_by_id_not_found(self):
        from sqlalchemy.exc import NoResultFound

        from src.exceptions import ObjectNotFoundException

        session = _make_session()
        result_mock = MagicMock()
        scalars = MagicMock()
        scalars.one.side_effect = NoResultFound()
        result_mock.scalars.return_value = scalars
        session.execute.return_value = result_mock

        repo = self._make_repo(session)
        with pytest.raises(ObjectNotFoundException):
            await repo.get_user_with_hashed_password_by_id(999)

    async def test_update_hashed_password(self):
        session = _make_session()
        session.execute.return_value = MagicMock()

        repo = self._make_repo(session)
        await repo.update_hashed_password(user_id=1, hashed_password="newhash")
        session.execute.assert_called_once()

    async def test_update_email_unique_violation(self):
        from asyncpg import UniqueViolationError
        from sqlalchemy.exc import IntegrityError

        from src.exceptions import ObjectAlreadyExistsException

        session = _make_session()
        cause = UniqueViolationError()
        exc = IntegrityError("stmt", {}, cause)
        exc.orig = MagicMock(__cause__=cause)
        session.execute.side_effect = exc

        repo = self._make_repo(session)
        with pytest.raises(ObjectAlreadyExistsException):
            await repo.update_email(user_id=1, new_email="taken@test.com")

    async def test_update_email_success(self):
        session = _make_session()
        session.execute.return_value = MagicMock()

        repo = self._make_repo(session)
        await repo.update_email(user_id=1, new_email="new@test.com")
        session.execute.assert_called_once()


# ─── BookingsRepository ───────────────────────────────────────────────────────


class TestBookingsRepository:
    def _make_repo(self, session=None):
        from src.repositories.bookings import BookingsRepository

        return BookingsRepository(session=session or _make_session())

    async def test_count_by_user(self):
        session = _make_session()
        session.execute.return_value = _scalar_result(5)

        repo = self._make_repo(session)
        assert await repo.count_by_user(user_id=1) == 5

    async def test_count_by_room(self):
        session = _make_session()
        session.execute.return_value = _scalar_result(3)

        repo = self._make_repo(session)
        assert await repo.count_by_room(room_id=1) == 3

    async def test_get_paginated_by_user(self):
        session = _make_session()
        orm_b = _make_orm_booking()
        session.execute.return_value = _scalars_result([orm_b])

        repo = self._make_repo(session)
        result = await repo.get_paginated_by_user(user_id=1, limit=10, offset=0)
        assert len(result) == 1

    async def test_get_paginated_by_user_empty(self):
        session = _make_session()
        session.execute.return_value = _scalars_result([])

        repo = self._make_repo(session)
        result = await repo.get_paginated_by_user(user_id=1, limit=10, offset=0)
        assert result == []

    async def test_add_booking_room_not_found(self):
        from src.exceptions import RoomNotFoundException
        from src.schemas.bookings import BookingAdd

        session = _make_session()
        # First execute (FOR UPDATE lock) returns None
        lock_result = MagicMock()
        lock_result.scalar_one_or_none.return_value = None
        session.execute.return_value = lock_result

        repo = self._make_repo(session)
        data = BookingAdd(
            user_id=1,
            room_id=99,
            date_from=date(2026, 5, 1),
            date_to=date(2026, 5, 5),
            price=1000,
        )
        with pytest.raises(RoomNotFoundException):
            await repo.add_booking(data, hotel_id=1)

    async def test_add_booking_no_rooms_available(self):
        from src.exceptions import AllRoomsAreBookedException
        from src.schemas.bookings import BookingAdd

        session = _make_session()
        orm_room = _make_orm_room(id=5)

        # Call 1: FOR UPDATE returns the room (exists)
        lock_result = MagicMock()
        lock_result.scalar_one_or_none.return_value = orm_room
        # Call 2: rooms_ids CTE returns empty list (no available rooms)
        ids_result = _scalars_result([])

        session.execute.side_effect = [lock_result, ids_result]

        repo = self._make_repo(session)
        data = BookingAdd(
            user_id=1,
            room_id=5,
            date_from=date(2026, 5, 1),
            date_to=date(2026, 5, 5),
            price=1000,
        )
        with pytest.raises(AllRoomsAreBookedException):
            await repo.add_booking(data, hotel_id=1)

    async def test_add_booking_success(self):
        from src.schemas.bookings import BookingAdd

        session = _make_session()
        orm_room = _make_orm_room(id=5)
        orm_booking = _make_orm_booking(id=100, room_id=5)

        # Call 1: FOR UPDATE lock
        lock_result = MagicMock()
        lock_result.scalar_one_or_none.return_value = orm_room
        # Call 2: available room IDs includes room_id=5
        ids_result = _scalars_result([5])
        # Call 3: INSERT booking (via BaseRepository.add)
        insert_result = _scalars_result([orm_booking])

        session.execute.side_effect = [lock_result, ids_result, insert_result]

        repo = self._make_repo(session)
        data = BookingAdd(
            user_id=1,
            room_id=5,
            date_from=date(2026, 5, 1),
            date_to=date(2026, 5, 5),
            price=1000,
        )
        result = await repo.add_booking(data, hotel_id=1)
        assert result.id == 100

    async def test_get_today_checkins_with_emails(self):
        session = _make_session()
        orm_b = _make_orm_booking(id=7)
        row = MagicMock()
        row.BookingsOrm = orm_b
        row.email = "guest@test.com"

        result_mock = MagicMock()
        result_mock.__iter__ = MagicMock(return_value=iter([row]))
        session.execute.return_value = result_mock

        repo = self._make_repo(session)
        rows = await repo.get_today_checkins_with_emails()
        assert len(rows) == 1
        assert rows[0]["email"] == "guest@test.com"


# ─── HotelsRepository ─────────────────────────────────────────────────────────


class TestHotelsRepository:
    def _make_repo(self, session=None):
        from src.repositories.hotels import HotelsRepository

        return HotelsRepository(session=session or _make_session())

    async def test_get_filtered_by_time_no_dates_no_hotels(self):
        session = _make_session()
        session.execute.return_value = _scalars_result([])

        repo = self._make_repo(session)
        result = await repo.get_filtered_by_time(date_from=None, date_to=None)
        assert result == []

    async def test_get_filtered_by_time_with_hotels_no_images(self):
        session = _make_session()
        orm_hotel = _make_orm_hotel(id=1)
        # Call 1: hotels query, Call 2: cover image query (returns empty)
        hotels_result = _scalars_result([orm_hotel])
        covers_result = MagicMock()
        covers_result.all.return_value = []
        session.execute.side_effect = [hotels_result, covers_result]

        repo = self._make_repo(session)
        result = await repo.get_filtered_by_time(date_from=None, date_to=None)
        assert len(result) == 1
        assert result[0].cover_image_url is None

    async def test_get_filtered_by_time_with_cover_image(self):
        session = _make_session()
        orm_hotel = _make_orm_hotel(id=1)
        hotels_result = _scalars_result([orm_hotel])
        covers_result = MagicMock()
        covers_result.all.return_value = [(1, "photo.jpg")]
        session.execute.side_effect = [hotels_result, covers_result]

        repo = self._make_repo(session)
        result = await repo.get_filtered_by_time(date_from=None, date_to=None)
        assert result[0].cover_image_url == "/static/images/photo.jpg"

    async def test_count_filtered_by_time(self):
        session = _make_session()
        session.execute.return_value = _scalar_result(7)

        repo = self._make_repo(session)
        count = await repo.count_filtered_by_time(date_from=None, date_to=None)
        assert count == 7

    async def test_get_autocomplete_combined(self):
        session = _make_session()
        cities_result = MagicMock()
        cities_result.all.return_value = [("Moscow",), ("Москва",)]
        hotels_result = MagicMock()
        hotels_result.all.return_value = [("Grand Hotel", "Moscow", "Red Square 1")]
        session.execute.side_effect = [cities_result, hotels_result]

        repo = self._make_repo(session)
        result = await repo.get_autocomplete_combined("Mos")
        assert result["locations"] == ["Moscow", "Москва"]
        assert result["hotels"][0]["title"] == "Grand Hotel"

    async def test_get_popular_locations(self):
        session = _make_session()
        result_mock = MagicMock()
        result_mock.all.return_value = [("Moscow",), ("SPB",), ("Kazan",)]
        session.execute.return_value = result_mock

        repo = self._make_repo(session)
        result = await repo.get_popular_locations(limit=3)
        assert result == ["Moscow", "SPB", "Kazan"]

    async def test_get_filtered_by_time_with_city_filter(self):
        session = _make_session()
        session.execute.return_value = _scalars_result([])

        repo = self._make_repo(session)
        result = await repo.get_filtered_by_time(date_from=None, date_to=None, city="Moscow")
        assert result == []
        session.execute.assert_called_once()

    async def test_get_filtered_by_time_with_search(self):
        session = _make_session()
        session.execute.return_value = _scalars_result([])

        repo = self._make_repo(session)
        result = await repo.get_filtered_by_time(date_from=None, date_to=None, search="grand")
        assert result == []


# ─── FacilitiesRepository / RoomsFacilitiesRepository ─────────────────────────


class TestFacilitiesRepository:
    def _make_repo(self, session=None):
        from src.repositories.facilities import FacilitiesRepository

        return FacilitiesRepository(session=session or _make_session())

    async def test_count(self):
        session = _make_session()
        session.execute.return_value = _scalar_result(12)

        repo = self._make_repo(session)
        assert await repo.count() == 12

    async def test_get_paginated(self):
        from src.models.facilities import FacilitiesOrm

        session = _make_session()
        orm_f = MagicMock(spec=FacilitiesOrm)
        orm_f.id = 1
        orm_f.title = "WiFi"
        session.execute.return_value = _scalars_result([orm_f])

        repo = self._make_repo(session)
        result = await repo.get_paginated(limit=10, offset=0)
        assert len(result) == 1

    async def test_get_paginated_empty(self):
        session = _make_session()
        session.execute.return_value = _scalars_result([])

        repo = self._make_repo(session)
        result = await repo.get_paginated(limit=10, offset=0)
        assert result == []


class TestRoomsFacilitiesRepository:
    def _make_repo(self, session=None):
        from src.repositories.facilities import RoomsFacilitiesRepository

        return RoomsFacilitiesRepository(session=session or _make_session())

    async def test_set_room_facilities_add_and_delete(self):
        """Should delete removed IDs and insert new ones."""
        session = _make_session()
        # Current facilities: [1, 2] → new: [2, 3] → delete [1], insert [3]
        existing = _scalars_result([1, 2])
        session.execute.side_effect = [existing, MagicMock(), MagicMock()]

        repo = self._make_repo(session)
        await repo.set_room_facilities(room_id=5, facilities_ids=[2, 3])
        # Should have 3 executes: SELECT + DELETE + INSERT
        assert session.execute.call_count == 3

    async def test_set_room_facilities_no_changes(self):
        """Same IDs → no delete/insert."""
        session = _make_session()
        existing = _scalars_result([1, 2])
        session.execute.side_effect = [existing]

        repo = self._make_repo(session)
        await repo.set_room_facilities(room_id=5, facilities_ids=[1, 2])
        assert session.execute.call_count == 1

    async def test_set_room_facilities_empty_clears_all(self):
        """Pass [] → delete all existing, insert nothing."""
        session = _make_session()
        existing = _scalars_result([1, 2])
        session.execute.side_effect = [existing, MagicMock()]

        repo = self._make_repo(session)
        await repo.set_room_facilities(room_id=5, facilities_ids=[])
        assert session.execute.call_count == 2  # SELECT + DELETE


# ─── RoomsRepository ──────────────────────────────────────────────────────────


class TestRoomsRepository:
    def _make_repo(self, session=None):
        from src.repositories.rooms import RoomsRepository

        return RoomsRepository(session=session or _make_session())

    async def test_count_by_hotel(self):
        session = _make_session()
        session.execute.return_value = _scalar_result(4)

        repo = self._make_repo(session)
        assert await repo.count_by_hotel(hotel_id=1) == 4

    async def test_get_one_with_rels_not_found(self):
        from sqlalchemy.exc import NoResultFound

        from src.exceptions import RoomNotFoundException

        session = _make_session()
        result_mock = MagicMock()
        result_mock.scalar_one.side_effect = NoResultFound()
        session.execute.return_value = result_mock

        repo = self._make_repo(session)
        with pytest.raises(RoomNotFoundException):
            await repo.get_one_with_rels(id=999, hotel_id=1)

    async def test_get_filtered_by_time_no_dates(self):
        session = _make_session()
        session.execute.return_value = _scalars_result([])

        repo = self._make_repo(session)
        result = await repo.get_filtered_by_time(hotel_id=1, date_from=None, date_to=None)
        assert result == []

    async def test_count_filtered_by_time_no_dates(self):
        session = _make_session()
        session.execute.return_value = _scalar_result(3)

        repo = self._make_repo(session)
        assert await repo.count_filtered_by_time(hotel_id=1, date_from=None, date_to=None) == 3

    async def test_count_filtered_by_time_with_dates(self):
        session = _make_session()
        session.execute.return_value = _scalar_result(2)

        repo = self._make_repo(session)
        count = await repo.count_filtered_by_time(
            hotel_id=1, date_from=date(2026, 5, 1), date_to=date(2026, 5, 10)
        )
        assert count == 2

    async def test_get_by_fields_found(self):
        session = _make_session()
        orm_room = _make_orm_room(id=3)
        session.execute.return_value = _scalars_result([orm_room])

        repo = self._make_repo(session)
        result = await repo.get_by_fields(
            hotel_id=1, title="Room", description="Desc", price=1000, quantity=2
        )
        assert result is not None

    async def test_get_by_fields_not_found(self):
        session = _make_session()
        result_mock = MagicMock()
        scalars = MagicMock()
        scalars.first.return_value = None
        result_mock.scalars.return_value = scalars
        session.execute.return_value = result_mock

        repo = self._make_repo(session)
        result = await repo.get_by_fields(
            hotel_id=1, title="Nope", description=None, price=999, quantity=1
        )
        assert result is None
