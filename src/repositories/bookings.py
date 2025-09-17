from src.repositories.mappers.mappers import BookingDataMapper
from src.models.bookings import BookingsOrm
from src.repositories.base import BaseRepository


class BookingsRepository(BaseRepository):
    model = BookingsOrm
    mapper = BookingDataMapper
