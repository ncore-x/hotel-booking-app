from src.models.facilities import FacilitiesOrm
from src.models.hotel_images import HotelImagesOrm
from src.models.hotels import HotelsOrm
from src.models.bookings import BookingsOrm
from src.models.rooms import RoomsOrm
from src.models.users import UsersOrm
from src.repositories.mappers.base import DataMapper
from src.schemas.bookings import Booking
from src.schemas.facilities import Facility
from src.schemas.hotels import Hotel
from src.schemas.images import HotelImage
from src.schemas.rooms import Room, RoomWithRels
from src.schemas.users import User


class HotelDataMapper(DataMapper):
    db_model = HotelsOrm
    schema = Hotel


class HotelImageDataMapper(DataMapper):
    db_model = HotelImagesOrm
    schema = HotelImage


class RoomDataMapper(DataMapper):
    db_model = RoomsOrm
    schema = Room


class RoomDataWithRelsMapper(DataMapper):
    db_model = RoomsOrm
    schema = RoomWithRels


class UserDataMapper(DataMapper):
    db_model = UsersOrm
    schema = User


class BookingDataMapper(DataMapper):
    db_model = BookingsOrm
    schema = Booking


class FacilityDataMapper(DataMapper):
    db_model = FacilitiesOrm
    schema = Facility
