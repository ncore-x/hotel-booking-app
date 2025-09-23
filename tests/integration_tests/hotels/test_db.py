from src.schemas.hotels import HotelAdd
from src.utils.db_manager import DBManager
from src.database import async_session_maker_null_pool


async def test_add_hotel():
    hotel_data = HotelAdd(title="Moscow Resort",
                          location="Москва, ул. Московская 111")
    async with DBManager(session_factory=async_session_maker_null_pool) as db:
        await db.hotels.add(hotel_data)
        await db.commit()
