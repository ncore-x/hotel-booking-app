from src.schemas.users import User
from src.models.users import UsersOrm
from repositories.base import BaseRepository


class UsersRepository(BaseRepository):
    model = UsersOrm
    schema = User
