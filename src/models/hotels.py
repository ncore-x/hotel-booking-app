import typing
from datetime import datetime

from sqlalchemy import String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base

if typing.TYPE_CHECKING:
    from src.models.hotel_images import HotelImagesOrm


class HotelsOrm(Base):
    __tablename__ = "hotels"
    __table_args__ = (
        UniqueConstraint("title", "city", "address", name="uq_hotels_title_city_address"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(100))
    city: Mapped[str]
    address: Mapped[str | None]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    images: Mapped[list["HotelImagesOrm"]] = relationship(
        "HotelImagesOrm",
        back_populates="hotel",
        cascade="all, delete-orphan",
    )
