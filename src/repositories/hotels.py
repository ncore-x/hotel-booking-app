from datetime import date
from sqlalchemy import select, func, literal

from src.repositories.mappers.mappers import HotelDataMapper
from src.models.hotel_images import HotelImagesOrm
from src.models.rooms import RoomsOrm
from src.repositories.base import BaseRepository
from src.models.hotels import HotelsOrm
from src.repositories.utils import rooms_ids_for_booking
from src.schemas.hotels import Hotel


class HotelsRepository(BaseRepository):
    model = HotelsOrm
    mapper = HotelDataMapper

    def _base_query(
        self,
        date_from: date | None,
        date_to: date | None,
        city=None,
        title=None,
        search=None,
        guests: int = 1,
    ):
        query = select(HotelsOrm)
        if date_from and date_to:
            rooms_ids_to_get = rooms_ids_for_booking(
                date_from=date_from, date_to=date_to, guests=guests
            )  # type: ignore[arg-type]
            hotels_ids_to_get = (
                select(RoomsOrm.hotel_id)
                .select_from(RoomsOrm)
                .filter(RoomsOrm.id.in_(rooms_ids_to_get))
            )
            query = query.filter(HotelsOrm.id.in_(hotels_ids_to_get))
        if search:
            q = search.strip().lower()
            # City match: city contains q  OR  q contains city (e.g. user typed "Южно-Сахалинская" → city "Южно-Сахалинск")
            city_match = func.lower(HotelsOrm.city).contains(q) | (
                func.strpos(func.lower(literal(q)), func.lower(HotelsOrm.city)) > 0
            )
            query = query.filter(
                city_match
                | func.lower(HotelsOrm.title).contains(q)
                | func.lower(func.coalesce(HotelsOrm.address, "")).contains(q)
            )
        else:
            if city:
                query = query.filter(func.lower(HotelsOrm.city).contains(city.strip().lower()))
            if title:
                query = query.filter(func.lower(HotelsOrm.title).contains(title.strip().lower()))
        return query

    async def get_filtered_by_time(
        self,
        date_from: date | None,
        date_to: date | None,
        city=None,
        title=None,
        search=None,
        limit=None,
        offset=None,
        sort_by: str = "id",
        order: str = "asc",
        guests: int = 1,
    ) -> list[Hotel]:
        query = self._base_query(date_from, date_to, city, title, search, guests)
        column = getattr(HotelsOrm, sort_by, HotelsOrm.id)
        query = query.order_by(column.asc() if order == "asc" else column.desc())
        query = query.limit(limit).offset(offset)
        result = await self.session.execute(query)
        hotels = [self.mapper.map_to_domain_entity(hotel) for hotel in result.scalars().all()]

        if hotels:
            hotel_ids = [h.id for h in hotels]
            cover_query = (
                select(HotelImagesOrm.hotel_id, HotelImagesOrm.filename)
                .where(HotelImagesOrm.hotel_id.in_(hotel_ids))
                .distinct(HotelImagesOrm.hotel_id)
                .order_by(HotelImagesOrm.hotel_id, HotelImagesOrm.id)
            )
            cover_result = await self.session.execute(cover_query)
            covers = {row[0]: row[1] for row in cover_result.all()}
            hotels = [
                h.model_copy(
                    update={
                        "cover_image_url": f"/static/images/{covers[h.id]}"
                        if h.id in covers
                        else None
                    }
                )
                for h in hotels
            ]

        return hotels

    async def count_filtered_by_time(
        self,
        date_from: date | None,
        date_to: date | None,
        city=None,
        title=None,
        search=None,
        guests: int = 1,
    ) -> int:
        base = self._base_query(date_from, date_to, city, title, search, guests)
        count_query = select(func.count()).select_from(base.subquery())
        result = await self.session.execute(count_query)
        return result.scalar_one()

    async def get_autocomplete_combined(self, q: str, limit: int = 5) -> dict:
        q_lower = q.strip().lower()

        city_query = (
            select(func.distinct(HotelsOrm.city))
            .filter(func.lower(HotelsOrm.city).contains(q_lower))
            .order_by(HotelsOrm.city)
            .limit(limit)
        )
        city_result = await self.session.execute(city_query)
        locations = [row[0] for row in city_result.all()]

        hotel_query = (
            select(HotelsOrm.title, HotelsOrm.city, HotelsOrm.address)
            .filter(
                func.lower(HotelsOrm.title).contains(q_lower)
                | func.lower(func.coalesce(HotelsOrm.address, "")).contains(q_lower)
            )
            .order_by(HotelsOrm.title)
            .limit(limit)
        )
        hotel_result = await self.session.execute(hotel_query)
        hotels = [
            {"title": row[0], "city": row[1], "address": row[2]} for row in hotel_result.all()
        ]

        return {"locations": locations, "hotels": hotels}

    async def get_popular_locations(self, limit: int = 8) -> list[str]:
        query = (
            select(HotelsOrm.city, func.count(HotelsOrm.id).label("cnt"))
            .group_by(HotelsOrm.city)
            .order_by(func.count(HotelsOrm.id).desc())
            .limit(limit)
        )
        result = await self.session.execute(query)
        return [row[0] for row in result.all()]
