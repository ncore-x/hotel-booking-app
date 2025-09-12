from models.bookings import BookingsOrm
from repositories.base import BaseRepository
from schemas.bookings import Booking


class BookingsRepository(BaseRepository):
    model = BookingsOrm
    schema = Booking
