from models.hotels import HotelsOrm
from repositories.base import BaseRepository


class HotelsRepository(BaseRepository):
    model = HotelsOrm
