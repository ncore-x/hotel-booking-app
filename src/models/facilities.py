import typing
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, String

from src.database import Base

if typing.TYPE_CHECKING:
    from src.models import RoomsOrm


class FacilitiesOrm(Base):
    __tablename__ = "facilities"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(100))

    rooms: Mapped[list["RoomsOrm"]] = relationship(  # type: ignore
        back_populates="facilities", secondary="rooms_facilities"
    )


class RoomsFacilitiesOrm(Base):
    __tablename__ = "rooms_facilities"

    room_id: Mapped[int] = mapped_column(ForeignKey(
        "rooms.id", ondelete="CASCADE"), primary_key=True)
    facility_id: Mapped[int] = mapped_column(
        ForeignKey("facilities.id"), primary_key=True)
