import typing

from sqlalchemy import String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base

if typing.TYPE_CHECKING:
    from src.models.hotel_images import HotelImagesOrm


class HotelsOrm(Base):
    __tablename__ = "hotels"
    __table_args__ = (UniqueConstraint("title", "location", name="uq_hotels_title_location"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(100))
    location: Mapped[str]

    images: Mapped[list["HotelImagesOrm"]] = relationship(
        "HotelImagesOrm",
        back_populates="hotel",
        cascade="all, delete-orphan",
    )
