from src.schemas.hotels import HotelAdd
from src.utils.db_manager import DBManager
from src.database import async_session_maker


async def test_add_hotel():
    hotel_add = HotelAdd(title="Moscow Resort",
                         location="Москва, ул. Московская 111")
    async with DBManager(session_factory=async_session_maker) as db:
        new_hotel_data = await db.hotels.add(hotel_add)
        print(f"{new_hotel_data=}")
