"""Unit tests for service layer (BookingService, RoomService, FacilityService, HotelService, ImagesService)."""

from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.exceptions import (
    CannotDeleteHotelWithRoomsException,
    CannotDeleteRoomWithBookingsException,
    CorruptedImageException,
    EmptyFileException,
    FacilityTitleEmptyException,
    FileTooLargeException,
    HotelNotFoundException,
    InvalidDateRangeException,
    ObjectAlreadyExistsException,
    ObjectNotFoundException,
    RoomNotFoundException,
    UnsupportedMediaTypeException,
)


# ─── Helpers ──────────────────────────────────────────────────────────────────


def _make_db(**overrides):
    """Create a mock DBManager with common repository mocks."""
    db = MagicMock()
    db.hotels = AsyncMock()
    db.rooms = AsyncMock()
    db.bookings = AsyncMock()
    db.facilities = AsyncMock()
    db.rooms_facilities = AsyncMock()
    db.hotel_images = AsyncMock()
    db.commit = AsyncMock()
    for k, v in overrides.items():
        setattr(db, k, v)
    return db


# ─── BookingService ──────────────────────────────────────────────────────────


class TestBookingService:
    def _make_service(self, db=None):
        from src.services.bookings import BookingService

        return BookingService(db=db or _make_db())

    async def test_add_booking_room_not_found(self):
        db = _make_db()
        db.rooms.get_one.side_effect = ObjectNotFoundException()
        svc = self._make_service(db)

        from src.schemas.bookings import BookingAddRequest

        data = BookingAddRequest(room_id=999, date_from=date(2026, 5, 1), date_to=date(2026, 5, 5))
        with pytest.raises(RoomNotFoundException):
            await svc.add_booking(user_id=1, booking_data=data)

    async def test_add_booking_success(self):
        db = _make_db()
        mock_room = MagicMock(id=1, hotel_id=10, price=5000)
        mock_hotel = MagicMock(id=10)
        mock_booking = MagicMock(id=100)
        db.rooms.get_one.return_value = mock_room
        db.hotels.get_one.return_value = mock_hotel
        db.bookings.add_booking.return_value = mock_booking

        svc = self._make_service(db)

        from src.schemas.bookings import BookingAddRequest

        data = BookingAddRequest(room_id=1, date_from=date(2026, 5, 1), date_to=date(2026, 5, 5))
        result = await svc.add_booking(user_id=1, booking_data=data)
        assert result is mock_booking
        db.commit.assert_called_once()

    async def test_get_my_bookings(self):
        db = _make_db()
        db.bookings.count_by_user.return_value = 25
        db.bookings.get_paginated_by_user.return_value = [MagicMock()] * 10
        svc = self._make_service(db)

        result = await svc.get_my_bookings(user_id=1, page=2, per_page=10)
        assert result.total == 25
        assert result.page == 2
        assert result.pages == 3

    async def test_get_booking_not_found(self):
        db = _make_db()
        db.bookings.get_one_or_none.return_value = None
        svc = self._make_service(db)

        with pytest.raises(ObjectNotFoundException):
            await svc.get_booking(user_id=1, booking_id=999)

    async def test_cancel_booking_not_found(self):
        db = _make_db()
        db.bookings.get_one_or_none.return_value = None
        svc = self._make_service(db)

        with pytest.raises(ObjectNotFoundException):
            await svc.cancel_booking(user_id=1, booking_id=999)

    async def test_cancel_booking_success(self):
        db = _make_db()
        db.bookings.get_one_or_none.return_value = MagicMock(id=1)
        svc = self._make_service(db)

        await svc.cancel_booking(user_id=1, booking_id=1)
        db.bookings.delete.assert_called_once()
        db.commit.assert_called_once()

    async def test_patch_booking_not_found(self):
        db = _make_db()
        db.bookings.get_one_or_none.return_value = None
        svc = self._make_service(db)

        from src.schemas.bookings import BookingPatchRequest

        with pytest.raises(ObjectNotFoundException):
            await svc.patch_booking(1, 999, BookingPatchRequest())

    async def test_patch_booking_invalid_dates(self):
        db = _make_db()
        # Existing booking: date_from=2027-05-01, date_to=2027-05-05
        # We patch only date_from to 2027-05-10 => new_date_from > existing date_to => InvalidDateRange
        mock_booking = MagicMock(
            id=1, room_id=10, date_from=date(2027, 5, 1), date_to=date(2027, 5, 5)
        )
        db.bookings.get_one_or_none.return_value = mock_booking
        svc = self._make_service(db)

        from src.schemas.bookings import BookingPatchRequest

        with pytest.raises(InvalidDateRangeException):
            await svc.patch_booking(1, 1, BookingPatchRequest(date_from=date(2027, 5, 10)))


# ─── FacilityService ─────────────────────────────────────────────────────────


class TestFacilityService:
    def _make_service(self, db=None):
        from src.services.facilities import FacilityService

        return FacilityService(db=db or _make_db())

    async def test_add_empty_title(self):
        from src.schemas.facilities import FacilityAdd

        svc = self._make_service()
        with pytest.raises(FacilityTitleEmptyException):
            await svc.facility_add(FacilityAdd(title="   "))

    async def test_add_success(self):
        from src.schemas.facilities import FacilityAdd

        db = _make_db()
        mock_fac = MagicMock(id=1, title="WiFi")
        db.facilities.add.return_value = mock_fac
        svc = self._make_service(db)

        result = await svc.facility_add(FacilityAdd(title="WiFi"))
        assert result is mock_fac
        db.commit.assert_called_once()

    async def test_add_duplicate(self):
        from src.schemas.facilities import FacilityAdd

        db = _make_db()
        db.facilities.add.side_effect = ObjectAlreadyExistsException()
        svc = self._make_service(db)

        with pytest.raises(ObjectAlreadyExistsException):
            await svc.facility_add(FacilityAdd(title="WiFi"))

    async def test_delete_not_found(self):
        db = _make_db()
        db.facilities.get_one.side_effect = ObjectNotFoundException()
        svc = self._make_service(db)

        with pytest.raises(ObjectNotFoundException):
            await svc.facility_delete(999)

    async def test_delete_success(self):
        db = _make_db()
        db.facilities.get_one.return_value = MagicMock(id=1)
        svc = self._make_service(db)

        await svc.facility_delete(1)
        db.facilities.delete.assert_called_once()
        db.commit.assert_called_once()

    async def test_get_facilities_pagination(self):
        db = _make_db()
        db.facilities.count.return_value = 55
        db.facilities.get_paginated.return_value = [MagicMock()] * 50
        svc = self._make_service(db)

        result = await svc.get_facilities(page=1, per_page=50)
        assert result.total == 55
        assert result.pages == 2


# ─── HotelService ────────────────────────────────────────────────────────────


class TestHotelService:
    def _make_service(self, db=None):
        from src.services.hotels import HotelService

        return HotelService(db=db or _make_db())

    async def test_get_hotel_with_check_not_found(self):
        db = _make_db()
        db.hotels.get_one.side_effect = ObjectNotFoundException()
        svc = self._make_service(db)

        with pytest.raises(HotelNotFoundException):
            await svc.get_hotel_with_check(999)

    async def test_get_hotel_with_check_success(self):
        db = _make_db()
        mock_hotel = MagicMock(id=1, title="Hotel A")
        db.hotels.get_one.return_value = mock_hotel
        svc = self._make_service(db)

        result = await svc.get_hotel_with_check(1)
        assert result is mock_hotel

    @patch("src.services.hotels.get_es_client", return_value=None)
    async def test_add_hotel(self, _):
        from src.schemas.hotels import HotelAdd

        db = _make_db()
        mock_hotel = MagicMock(id=1, title="New Hotel", city="Moscow", address="Addr")
        db.hotels.add.return_value = mock_hotel
        svc = self._make_service(db)

        result = await svc.add_hotel(HotelAdd(title="New Hotel", city="Moscow"))
        assert result is mock_hotel
        db.commit.assert_called_once()

    async def test_delete_hotel_with_rooms(self):
        db = _make_db()
        db.hotels.get_one.return_value = MagicMock(id=1)
        db.rooms.count_by_hotel.return_value = 5
        svc = self._make_service(db)

        with pytest.raises(CannotDeleteHotelWithRoomsException):
            await svc.delete_hotel(1)

    @patch("src.services.hotels.get_es_client", return_value=None)
    async def test_delete_hotel_success(self, _):
        db = _make_db()
        db.hotels.get_one.return_value = MagicMock(id=1)
        db.rooms.count_by_hotel.return_value = 0
        svc = self._make_service(db)

        await svc.delete_hotel(1)
        db.hotels.delete.assert_called_once()
        db.commit.assert_called_once()

    @patch("src.services.hotels.get_es_client", return_value=None)
    async def test_autocomplete_no_es(self, _):
        db = _make_db()
        db.hotels.get_autocomplete_combined.return_value = {"locations": [], "hotels": []}
        svc = self._make_service(db)

        await svc.autocomplete_combined("test")
        db.hotels.get_autocomplete_combined.assert_called_once_with("test")

    @patch("src.services.hotels.get_es_client")
    @patch("src.services.hotels.es_hotels")
    async def test_autocomplete_with_es(self, mock_es_hotels, mock_get_client):
        mock_client = AsyncMock()
        mock_get_client.return_value = mock_client
        mock_es_hotels.autocomplete = AsyncMock(
            return_value={"locations": ["Moscow"], "hotels": []}
        )
        svc = self._make_service()

        result = await svc.autocomplete_combined("Mos")
        assert result["locations"] == ["Moscow"]

    @patch("src.services.hotels.get_es_client")
    @patch("src.services.hotels.es_hotels")
    async def test_autocomplete_es_fallback(self, mock_es_hotels, mock_get_client):
        mock_client = AsyncMock()
        mock_get_client.return_value = mock_client
        mock_es_hotels.autocomplete.side_effect = Exception("ES down")
        db = _make_db()
        db.hotels.get_autocomplete_combined.return_value = {"locations": [], "hotels": []}
        svc = self._make_service(db)

        await svc.autocomplete_combined("test")
        db.hotels.get_autocomplete_combined.assert_called_once()

    async def test_popular_locations(self):
        db = _make_db()
        db.hotels.get_popular_locations.return_value = ["Moscow", "SPB"]
        svc = self._make_service(db)

        result = await svc.popular_locations(limit=5)
        assert result == ["Moscow", "SPB"]


# ─── RoomService ─────────────────────────────────────────────────────────────


class TestRoomService:
    def _make_service(self, db=None):
        from src.services.rooms import RoomService

        return RoomService(db=db or _make_db())

    async def test_get_room_with_check_not_found(self):
        db = _make_db()
        db.rooms.get_one.side_effect = ObjectNotFoundException()
        svc = self._make_service(db)

        with pytest.raises(RoomNotFoundException):
            await svc.get_room_with_check(999, hotel_id=1)

    async def test_get_room_with_check_success(self):
        db = _make_db()
        mock_room = MagicMock(id=1)
        db.rooms.get_one.return_value = mock_room
        svc = self._make_service(db)

        result = await svc.get_room_with_check(1, hotel_id=1)
        assert result is mock_room

    async def test_get_room_with_check_no_hotel(self):
        db = _make_db()
        mock_room = MagicMock(id=1)
        db.rooms.get_one.return_value = mock_room
        svc = self._make_service(db)

        result = await svc.get_room_with_check(1, hotel_id=None)
        assert result is mock_room

    async def test_delete_room_with_bookings(self):
        db = _make_db()
        db.hotels.get_one.return_value = MagicMock(id=1)
        db.rooms.get_one.return_value = MagicMock(id=1)
        db.bookings.count_by_room.return_value = 3
        svc = self._make_service(db)

        with pytest.raises(CannotDeleteRoomWithBookingsException):
            await svc.delete_room(hotel_id=1, room_id=1)

    async def test_delete_room_success(self):
        db = _make_db()
        db.hotels.get_one.return_value = MagicMock(id=1)
        db.rooms.get_one.return_value = MagicMock(id=1)
        db.bookings.count_by_room.return_value = 0
        svc = self._make_service(db)

        await svc.delete_room(hotel_id=1, room_id=1)
        db.rooms.delete.assert_called_once()
        db.commit.assert_called_once()

    async def test_get_filtered_by_time_invalid_dates(self):
        db = _make_db()
        db.hotels.get_one.return_value = MagicMock(id=1)
        svc = self._make_service(db)

        with pytest.raises(InvalidDateRangeException):
            await svc.get_filtered_by_time(
                hotel_id=1, date_from=date(2026, 5, 10), date_to=date(2026, 5, 1)
            )

    async def test_create_room_facility_not_found(self):
        db = _make_db()
        db.hotels.get_one.return_value = MagicMock(id=1)
        db.facilities.get_one.side_effect = ObjectNotFoundException()
        svc = self._make_service(db)

        from src.schemas.rooms import RoomAddRequest

        data = RoomAddRequest(
            title="Room 1", description="Desc", price=1000, quantity=2, facilities_ids=[999]
        )
        with pytest.raises(ObjectNotFoundException):
            await svc.create_room(hotel_id=1, room_data=data)


# ─── ImagesService ───────────────────────────────────────────────────────────


def _make_upload_file(
    content: bytes, content_type: str = "image/jpeg", filename: str = "photo.jpg"
):
    """Create a mock UploadFile."""
    mock_file = AsyncMock()
    mock_file.content_type = content_type
    mock_file.filename = filename
    mock_file.read = AsyncMock(return_value=content)
    return mock_file


def _minimal_jpeg() -> bytes:
    """Generate a minimal valid JPEG in memory."""
    import io

    from PIL import Image

    buf = io.BytesIO()
    img = Image.new("RGB", (100, 80), color="blue")
    img.save(buf, format="JPEG")
    img.close()
    return buf.getvalue()


def _minimal_png_rgba() -> bytes:
    """Generate a minimal RGBA PNG in memory."""
    import io

    from PIL import Image

    buf = io.BytesIO()
    img = Image.new("RGBA", (100, 80), color=(0, 0, 255, 128))
    img.save(buf, format="PNG")
    img.close()
    return buf.getvalue()


class TestImagesService:
    def _make_service(self, db=None):
        from src.services.images import ImagesService

        return ImagesService(db=db or _make_db())

    async def test_upload_hotel_not_found(self):
        db = _make_db()
        db.hotels.get_one.side_effect = ObjectNotFoundException()
        svc = self._make_service(db)

        file = _make_upload_file(b"data")
        with pytest.raises(HotelNotFoundException):
            await svc.upload_image(hotel_id=999, file=file)

    async def test_upload_unsupported_mime(self):
        db = _make_db()
        db.hotels.get_one.return_value = MagicMock(id=1)
        svc = self._make_service(db)

        file = _make_upload_file(b"data", content_type="application/pdf")
        with pytest.raises(UnsupportedMediaTypeException):
            await svc.upload_image(hotel_id=1, file=file)

    async def test_upload_empty_file(self):
        db = _make_db()
        db.hotels.get_one.return_value = MagicMock(id=1)
        svc = self._make_service(db)

        file = _make_upload_file(b"", content_type="image/jpeg")
        with pytest.raises(EmptyFileException):
            await svc.upload_image(hotel_id=1, file=file)

    async def test_upload_too_large(self):
        db = _make_db()
        db.hotels.get_one.return_value = MagicMock(id=1)
        svc = self._make_service(db)

        big_content = b"x" * (5_242_880 + 1)  # > 5MB
        file = _make_upload_file(big_content, content_type="image/jpeg")
        with pytest.raises(FileTooLargeException):
            await svc.upload_image(hotel_id=1, file=file)

    async def test_upload_corrupted_image(self):
        db = _make_db()
        db.hotels.get_one.return_value = MagicMock(id=1)
        svc = self._make_service(db)

        file = _make_upload_file(b"not-an-image-at-all", content_type="image/jpeg")
        with pytest.raises(CorruptedImageException):
            await svc.upload_image(hotel_id=1, file=file)

    async def test_upload_unsupported_format(self):
        """Valid image but unsupported format (e.g. BMP detected)."""
        import io

        from PIL import Image

        buf = io.BytesIO()
        img = Image.new("RGB", (10, 10), color="red")
        img.save(buf, format="BMP")
        img.close()

        db = _make_db()
        db.hotels.get_one.return_value = MagicMock(id=1)
        svc = self._make_service(db)

        # content_type empty so it passes the MIME check, but BMP format is not allowed
        file = _make_upload_file(buf.getvalue(), content_type="")
        with pytest.raises(UnsupportedMediaTypeException):
            await svc.upload_image(hotel_id=1, file=file)

    @patch("src.services.images.resize_image")
    async def test_upload_success(self, mock_resize):
        db = _make_db()
        db.hotels.get_one.return_value = MagicMock(id=1)
        mock_record = MagicMock(id=42)
        db.hotel_images.add.return_value = mock_record
        svc = self._make_service(db)

        jpeg_bytes = _minimal_jpeg()
        file = _make_upload_file(jpeg_bytes, content_type="image/jpeg")

        with patch("src.services.images.settings") as mock_settings:
            import tempfile
            from pathlib import Path

            tmp_dir = Path(tempfile.mkdtemp())
            mock_settings.IMAGES_DIR = tmp_dir
            mock_settings.MAX_IMAGE_SIZE_BYTES = 5_242_880

            result = await svc.upload_image(hotel_id=1, file=file)

        assert result.id == 42
        assert result.hotel_id == 1
        assert result.content_type == "image/jpeg"
        assert result.width == 100
        assert result.height == 80
        db.hotel_images.add.assert_called_once()
        db.commit.assert_called_once()
        mock_resize.delay.assert_called_once()

    @patch("src.services.images.resize_image")
    async def test_upload_db_failure_cleans_file(self, mock_resize):
        db = _make_db()
        db.hotels.get_one.return_value = MagicMock(id=1)
        db.hotel_images.add.side_effect = Exception("DB error")
        svc = self._make_service(db)

        jpeg_bytes = _minimal_jpeg()
        file = _make_upload_file(jpeg_bytes, content_type="image/jpeg")

        with (
            patch("src.services.images.settings") as mock_settings,
            pytest.raises(Exception, match="DB error"),
        ):
            import tempfile
            from pathlib import Path

            tmp_dir = Path(tempfile.mkdtemp())
            mock_settings.IMAGES_DIR = tmp_dir
            mock_settings.MAX_IMAGE_SIZE_BYTES = 5_242_880

            await svc.upload_image(hotel_id=1, file=file)

    @patch("src.services.images.resize_image")
    async def test_upload_celery_unavailable(self, mock_resize):
        """Celery down should not fail the upload."""
        mock_resize.delay.side_effect = Exception("Celery down")

        db = _make_db()
        db.hotels.get_one.return_value = MagicMock(id=1)
        mock_record = MagicMock(id=42)
        db.hotel_images.add.return_value = mock_record
        svc = self._make_service(db)

        jpeg_bytes = _minimal_jpeg()
        file = _make_upload_file(jpeg_bytes, content_type="image/jpeg")

        with patch("src.services.images.settings") as mock_settings:
            import tempfile
            from pathlib import Path

            tmp_dir = Path(tempfile.mkdtemp())
            mock_settings.IMAGES_DIR = tmp_dir
            mock_settings.MAX_IMAGE_SIZE_BYTES = 5_242_880

            result = await svc.upload_image(hotel_id=1, file=file)

        assert result.id == 42  # upload still succeeds

    @patch("src.services.images.resize_image")
    async def test_upload_png(self, mock_resize):
        db = _make_db()
        db.hotels.get_one.return_value = MagicMock(id=1)
        mock_record = MagicMock(id=10)
        db.hotel_images.add.return_value = mock_record
        svc = self._make_service(db)

        png_bytes = _minimal_png_rgba()
        file = _make_upload_file(png_bytes, content_type="image/png", filename="photo.png")

        with patch("src.services.images.settings") as mock_settings:
            import tempfile
            from pathlib import Path

            tmp_dir = Path(tempfile.mkdtemp())
            mock_settings.IMAGES_DIR = tmp_dir
            mock_settings.MAX_IMAGE_SIZE_BYTES = 5_242_880

            result = await svc.upload_image(hotel_id=1, file=file)

        assert result.content_type == "image/png"
        assert result.width == 100

    @patch("src.services.images.resize_image")
    async def test_upload_verify_exception_raises_corrupted(self, mock_resize):
        """Non-UnidentifiedImageError during img.verify() → CorruptedImageException."""
        import io

        from PIL import Image
        from unittest.mock import patch as _patch

        db = _make_db()
        db.hotels.get_one.return_value = MagicMock(id=1)
        svc = self._make_service(db)

        # Build a valid JPEG so it passes MIME check and size check,
        # but make img.verify() raise a generic Exception (not UnidentifiedImageError)
        buf = io.BytesIO()
        Image.new("RGB", (10, 10)).save(buf, format="JPEG")
        jpeg_bytes = buf.getvalue()
        file = _make_upload_file(jpeg_bytes, content_type="image/jpeg")

        with (
            patch("src.services.images.settings") as mock_settings,
            _patch("src.services.images.Image.open") as mock_open,
            pytest.raises(CorruptedImageException),
        ):
            mock_settings.MAX_IMAGE_SIZE_BYTES = 5_242_880
            mock_settings.IMAGES_DIR = __import__("pathlib").Path("/tmp/test_images")
            img_mock = MagicMock()
            img_mock.verify.side_effect = Exception("unexpected PIL error")
            mock_open.return_value = img_mock
            await svc.upload_image(hotel_id=1, file=file)

    @patch("src.services.images.resize_image")
    async def test_upload_meta_read_exception_raises_corrupted(self, mock_resize):
        """Exception during metadata read (second Image.open) → CorruptedImageException."""
        import io

        from PIL import Image
        from unittest.mock import patch as _patch

        db = _make_db()
        db.hotels.get_one.return_value = MagicMock(id=1)
        svc = self._make_service(db)

        buf = io.BytesIO()
        Image.new("RGB", (10, 10)).save(buf, format="JPEG")
        jpeg_bytes = buf.getvalue()
        file = _make_upload_file(jpeg_bytes, content_type="image/jpeg")

        call_count = 0

        def _side_effect(bio):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # First call (verify): return real mock that passes verify()
                m = MagicMock()
                m.verify.return_value = None
                return m
            # Second call (metadata): raise generic error
            raise Exception("cannot read metadata")

        with (
            patch("src.services.images.settings") as mock_settings,
            _patch("src.services.images.Image.open", side_effect=_side_effect),
            pytest.raises(CorruptedImageException),
        ):
            mock_settings.MAX_IMAGE_SIZE_BYTES = 5_242_880
            mock_settings.IMAGES_DIR = __import__("pathlib").Path("/tmp/test_images")
            await svc.upload_image(hotel_id=1, file=file)

    @patch("src.services.images.resize_image")
    async def test_upload_write_file_exception_raises_corrupted(self, mock_resize):
        """asyncio.to_thread failure → CorruptedImageException."""
        import tempfile
        from pathlib import Path
        from unittest.mock import patch as _patch

        db = _make_db()
        db.hotels.get_one.return_value = MagicMock(id=1)
        svc = self._make_service(db)

        jpeg_bytes = _minimal_jpeg()
        file = _make_upload_file(jpeg_bytes, content_type="image/jpeg")

        with (
            patch("src.services.images.settings") as mock_settings,
            _patch("src.services.images.asyncio.to_thread", side_effect=Exception("disk full")),
            pytest.raises(CorruptedImageException),
        ):
            tmp_dir = Path(tempfile.mkdtemp())
            mock_settings.IMAGES_DIR = tmp_dir
            mock_settings.MAX_IMAGE_SIZE_BYTES = 5_242_880
            await svc.upload_image(hotel_id=1, file=file)

    @patch("src.services.images.resize_image")
    async def test_upload_db_failure_cleanup_error_logged(self, mock_resize):
        """If file cleanup itself fails after DB error, it logs and re-raises DB error."""
        import tempfile
        from pathlib import Path
        from unittest.mock import patch as _patch

        db = _make_db()
        db.hotels.get_one.return_value = MagicMock(id=1)
        db.hotel_images.add.side_effect = Exception("DB error")
        svc = self._make_service(db)

        jpeg_bytes = _minimal_jpeg()
        file = _make_upload_file(jpeg_bytes, content_type="image/jpeg")

        with (
            patch("src.services.images.settings") as mock_settings,
            # Make unlink raise to hit line 104 (cleanup warning)
            _patch("pathlib.Path.unlink", side_effect=OSError("permission denied")),
            pytest.raises(Exception, match="DB error"),
        ):
            tmp_dir = Path(tempfile.mkdtemp())
            mock_settings.IMAGES_DIR = tmp_dir
            mock_settings.MAX_IMAGE_SIZE_BYTES = 5_242_880
            await svc.upload_image(hotel_id=1, file=file)

    async def test_get_hotel_images_hotel_not_found(self):
        db = _make_db()
        db.hotels.get_one.side_effect = ObjectNotFoundException()
        svc = self._make_service(db)

        with pytest.raises(HotelNotFoundException):
            await svc.get_hotel_images(hotel_id=999)

    async def test_get_hotel_images_success(self):
        db = _make_db()
        db.hotels.get_one.return_value = MagicMock(id=1)
        mock_images = [MagicMock(id=1), MagicMock(id=2)]
        db.hotel_images.get_filtered.return_value = mock_images
        svc = self._make_service(db)

        result = await svc.get_hotel_images(hotel_id=1)
        assert result == mock_images
        db.hotel_images.get_filtered.assert_called_once_with(hotel_id=1)


# ─── RoomService (create / put / patch) ─────────────────────────────────────


class TestRoomServiceCRUD:
    def _make_service(self, db=None):
        from src.services.rooms import RoomService

        return RoomService(db=db or _make_db())

    async def test_get_filtered_by_time_success(self):
        db = _make_db()
        db.hotels.get_one.return_value = MagicMock(id=1)
        db.rooms.count_filtered_by_time.return_value = 3
        db.rooms.get_filtered_by_time.return_value = [MagicMock()] * 3
        svc = self._make_service(db)

        result = await svc.get_filtered_by_time(
            hotel_id=1, date_from=date(2026, 5, 1), date_to=date(2026, 5, 10)
        )
        assert result.total == 3
        assert result.pages == 1

    async def test_get_room_success(self):
        db = _make_db()
        db.hotels.get_one.return_value = MagicMock(id=1)
        mock_room = MagicMock(id=5)
        db.rooms.get_one_with_rels.return_value = mock_room
        svc = self._make_service(db)

        result = await svc.get_room(room_id=5, hotel_id=1)
        assert result is mock_room

    async def test_create_room_success(self):
        from src.schemas.rooms import RoomAddRequest

        db = _make_db()
        db.hotels.get_one.return_value = MagicMock(id=1)
        db.facilities.get_one.return_value = MagicMock(id=10)
        mock_room = MagicMock(id=1)
        db.rooms.add.return_value = mock_room
        mock_room_rels = MagicMock(id=1)
        db.rooms.get_one_with_rels.return_value = mock_room_rels
        svc = self._make_service(db)

        data = RoomAddRequest(
            title="Room 1", description="Desc", price=1000, quantity=2, facilities_ids=[10]
        )
        result = await svc.create_room(hotel_id=1, room_data=data)
        assert result is mock_room_rels
        db.rooms_facilities.add_bulk.assert_called_once()
        db.commit.assert_called_once()

    async def test_create_room_no_facilities(self):
        from src.schemas.rooms import RoomAddRequest

        db = _make_db()
        db.hotels.get_one.return_value = MagicMock(id=1)
        mock_room = MagicMock(id=1)
        db.rooms.add.return_value = mock_room
        db.rooms.get_one_with_rels.return_value = MagicMock(id=1)
        svc = self._make_service(db)

        data = RoomAddRequest(
            title="Room 1", description="Desc", price=1000, quantity=2, facilities_ids=[]
        )
        await svc.create_room(hotel_id=1, room_data=data)
        db.rooms_facilities.add_bulk.assert_not_called()

    async def test_room_put_update_success(self):
        from src.schemas.rooms import RoomAddRequest

        db = _make_db()
        db.hotels.get_one.return_value = MagicMock(id=1)
        db.rooms.get_one.return_value = MagicMock(id=5)
        db.facilities.get_one.return_value = MagicMock(id=10)
        mock_room_rels = MagicMock(id=5)
        db.rooms.get_one_with_rels.return_value = mock_room_rels
        svc = self._make_service(db)

        data = RoomAddRequest(
            title="Updated", description="New desc", price=2000, quantity=1, facilities_ids=[10]
        )
        result = await svc.room_put_update(hotel_id=1, room_id=5, room_data=data)
        assert result is mock_room_rels
        db.rooms.edit.assert_called_once()
        db.rooms_facilities.set_room_facilities.assert_called_once()
        db.commit.assert_called_once()

    async def test_room_put_update_facility_not_found(self):
        from src.schemas.rooms import RoomAddRequest

        db = _make_db()
        db.hotels.get_one.return_value = MagicMock(id=1)
        db.rooms.get_one.return_value = MagicMock(id=5)
        db.facilities.get_one.side_effect = ObjectNotFoundException()
        svc = self._make_service(db)

        data = RoomAddRequest(
            title="Updated", description="Desc", price=2000, quantity=1, facilities_ids=[999]
        )
        with pytest.raises(ObjectNotFoundException):
            await svc.room_put_update(hotel_id=1, room_id=5, room_data=data)

    async def test_room_patch_update_success(self):
        from src.schemas.rooms import RoomPatchRequest

        db = _make_db()
        db.hotels.get_one.return_value = MagicMock(id=1)
        db.rooms.get_one.return_value = MagicMock(id=5)
        mock_room_rels = MagicMock(id=5)
        db.rooms.get_one_with_rels.return_value = mock_room_rels
        svc = self._make_service(db)

        data = RoomPatchRequest(title="Patched title")
        result = await svc.room_patch_update(hotel_id=1, room_id=5, room_data=data)
        assert result is mock_room_rels
        db.rooms.edit.assert_called_once()
        db.commit.assert_called_once()

    async def test_room_patch_update_with_facilities(self):
        from src.schemas.rooms import RoomPatchRequest

        db = _make_db()
        db.hotels.get_one.return_value = MagicMock(id=1)
        db.rooms.get_one.return_value = MagicMock(id=5)
        db.facilities.get_one.return_value = MagicMock(id=10)
        db.rooms.get_one_with_rels.return_value = MagicMock(id=5)
        svc = self._make_service(db)

        data = RoomPatchRequest(facilities_ids=[10])
        await svc.room_patch_update(hotel_id=1, room_id=5, room_data=data)
        db.rooms_facilities.set_room_facilities.assert_called_once()

    async def test_room_patch_update_facility_not_found(self):
        from src.schemas.rooms import RoomPatchRequest

        db = _make_db()
        db.hotels.get_one.return_value = MagicMock(id=1)
        db.rooms.get_one.return_value = MagicMock(id=5)
        db.facilities.get_one.side_effect = ObjectNotFoundException()
        svc = self._make_service(db)

        data = RoomPatchRequest(facilities_ids=[999])
        with pytest.raises(ObjectNotFoundException):
            await svc.room_patch_update(hotel_id=1, room_id=5, room_data=data)


# ─── HotelService (put / patch / es_index / es_remove) ──────────────────────


class TestHotelServiceCRUD:
    def _make_service(self, db=None):
        from src.services.hotels import HotelService

        return HotelService(db=db or _make_db())

    @patch("src.services.hotels.get_es_client", return_value=None)
    async def test_hotel_put_update_no_es(self, _):
        from src.schemas.hotels import HotelAdd

        db = _make_db()
        mock_hotel = MagicMock(id=1, title="Updated", city="SPB", address="Addr")
        db.hotels.get_one.return_value = mock_hotel
        svc = self._make_service(db)

        result = await svc.hotel_put_update(1, HotelAdd(title="Updated", city="SPB"))
        assert result is mock_hotel
        db.hotels.edit.assert_called_once()
        db.commit.assert_called_once()

    @patch("src.services.hotels.get_es_client", return_value=None)
    async def test_hotel_patch_update_no_es(self, _):
        from src.schemas.hotels import HotelPatch

        db = _make_db()
        mock_hotel = MagicMock(id=1, title="Patched", city="Moscow", address=None)
        db.hotels.get_one.return_value = mock_hotel
        svc = self._make_service(db)

        result = await svc.hotel_patch_update(1, HotelPatch(title="Patched"), exclude_unset=True)
        assert result is mock_hotel
        db.hotels.edit.assert_called_once()
        db.commit.assert_called_once()

    @patch("src.services.hotels.es_hotels")
    @patch("src.services.hotels.get_es_client")
    async def test_es_index_success(self, mock_get_client, mock_es_hotels):
        mock_client = AsyncMock()
        mock_get_client.return_value = mock_client
        mock_es_hotels.index_hotel = AsyncMock()

        from src.schemas.hotels import HotelAdd

        db = _make_db()
        mock_hotel = MagicMock(id=1, title="H", city="C", address="A")
        db.hotels.add.return_value = mock_hotel
        svc = self._make_service(db)

        await svc.add_hotel(HotelAdd(title="H", city="C"))
        mock_es_hotels.index_hotel.assert_called_once_with(mock_client, 1, "H", "C", "A")

    @patch("src.services.hotels.es_hotels")
    @patch("src.services.hotels.get_es_client")
    async def test_es_index_failure_logged(self, mock_get_client, mock_es_hotels):
        mock_client = AsyncMock()
        mock_get_client.return_value = mock_client
        mock_es_hotels.index_hotel = AsyncMock(side_effect=Exception("ES down"))

        from src.schemas.hotels import HotelAdd

        db = _make_db()
        mock_hotel = MagicMock(id=1, title="H", city="C", address="A")
        db.hotels.add.return_value = mock_hotel
        svc = self._make_service(db)

        # Should not raise — ES failure is logged, not propagated
        result = await svc.add_hotel(HotelAdd(title="H", city="C"))
        assert result is mock_hotel

    @patch("src.services.hotels.es_hotels")
    @patch("src.services.hotels.get_es_client")
    async def test_es_remove_success(self, mock_get_client, mock_es_hotels):
        mock_client = AsyncMock()
        mock_get_client.return_value = mock_client
        mock_es_hotels.remove_hotel = AsyncMock()

        db = _make_db()
        db.hotels.get_one.return_value = MagicMock(id=1)
        db.rooms.count_by_hotel.return_value = 0
        svc = self._make_service(db)

        await svc.delete_hotel(1)
        mock_es_hotels.remove_hotel.assert_called_once_with(mock_client, 1)

    @patch("src.services.hotels.es_hotels")
    @patch("src.services.hotels.get_es_client")
    async def test_es_remove_failure_logged(self, mock_get_client, mock_es_hotels):
        mock_client = AsyncMock()
        mock_get_client.return_value = mock_client
        mock_es_hotels.remove_hotel = AsyncMock(side_effect=Exception("ES down"))

        db = _make_db()
        db.hotels.get_one.return_value = MagicMock(id=1)
        db.rooms.count_by_hotel.return_value = 0
        svc = self._make_service(db)

        # Should not raise
        await svc.delete_hotel(1)

    async def test_get_filtered_by_time(self):
        db = _make_db()
        db.hotels.get_filtered_by_time.return_value = [MagicMock()] * 5
        db.hotels.count_filtered_by_time.return_value = 15
        svc = self._make_service(db)

        pagination = MagicMock(page=1, per_page=5)
        result = await svc.get_filtered_by_time(
            pagination, city="Moscow", title=None, date_from=None, date_to=None
        )
        assert result.total == 15
        assert result.pages == 3


# ─── BookingService (patch success) ─────────────────────────────────────────


class TestBookingServicePatch:
    def _make_service(self, db=None):
        from src.services.bookings import BookingService

        return BookingService(db=db or _make_db())

    async def test_patch_booking_success(self):
        from src.schemas.bookings import BookingPatchRequest

        db = _make_db()
        mock_booking = MagicMock(
            id=1, room_id=10, date_from=date(2027, 5, 1), date_to=date(2027, 5, 10)
        )
        db.bookings.get_one_or_none.return_value = mock_booking
        mock_room = MagicMock(id=10, hotel_id=20, price=5000)
        db.rooms.get_one.return_value = mock_room
        mock_hotel = MagicMock(id=20)
        db.hotels.get_one.return_value = mock_hotel
        mock_new_booking = MagicMock(id=2)
        db.bookings.add_booking.return_value = mock_new_booking
        svc = self._make_service(db)

        result = await svc.patch_booking(
            user_id=1, booking_id=1, data=BookingPatchRequest(date_to=date(2027, 5, 8))
        )
        assert result is mock_new_booking
        db.bookings.delete.assert_called_once()
        db.bookings.add_booking.assert_called_once()
        db.commit.assert_called_once()

    async def test_get_booking_success(self):
        db = _make_db()
        mock_booking = MagicMock(id=1)
        db.bookings.get_one_or_none.return_value = mock_booking
        svc = self._make_service(db)

        result = await svc.get_booking(user_id=1, booking_id=1)
        assert result is mock_booking
