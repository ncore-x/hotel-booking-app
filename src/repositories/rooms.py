from models.rooms import RoomsOrm
from repositories.base import BaseRepository


class RoomsRepository(BaseRepository):
    model = RoomsOrm
