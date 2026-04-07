import logging
from elasticsearch import AsyncElasticsearch, NotFoundError

logger = logging.getLogger(__name__)

INDEX = "hotels"

_MAPPING = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0,
    },
    "mappings": {
        "properties": {
            "id": {"type": "integer"},
            "title": {"type": "search_as_you_type"},
            "city": {"type": "search_as_you_type"},
            "city_keyword": {"type": "keyword"},
            "address": {"type": "text"},
        }
    },
}


async def ensure_index(es: AsyncElasticsearch) -> None:
    if not await es.indices.exists(index=INDEX):
        await es.indices.create(index=INDEX, **_MAPPING)
        logger.info("Elasticsearch: создан индекс '%s'", INDEX)


async def reindex_all(es: AsyncElasticsearch, hotels: list[dict]) -> None:
    await ensure_index(es)
    if not hotels:
        return
    operations = []
    for h in hotels:
        operations.append({"index": {"_index": INDEX, "_id": str(h["id"])}})
        operations.append(
            {
                "id": h["id"],
                "title": h["title"],
                "city": h["city"],
                "city_keyword": h["city"],
                "address": h.get("address") or "",
            }
        )
    await es.bulk(operations=operations)
    logger.info("Elasticsearch: проиндексировано %d отелей", len(hotels))


async def index_hotel(
    es: AsyncElasticsearch,
    hotel_id: int,
    title: str,
    city: str,
    address: str | None,
) -> None:
    await ensure_index(es)
    await es.index(
        index=INDEX,
        id=str(hotel_id),
        document={
            "id": hotel_id,
            "title": title,
            "city": city,
            "city_keyword": city,
            "address": address or "",
        },
    )


async def remove_hotel(es: AsyncElasticsearch, hotel_id: int) -> None:
    try:
        await es.delete(index=INDEX, id=str(hotel_id))
    except NotFoundError:
        pass


async def autocomplete(es: AsyncElasticsearch, q: str, limit: int = 5) -> dict:
    city_fields = ["city", "city._2gram", "city._3gram"]
    title_fields = ["title", "title._2gram", "title._3gram"]

    # Unique cities via terms aggregation
    city_resp = await es.search(
        index=INDEX,
        size=0,
        query={
            "multi_match": {
                "query": q,
                "type": "bool_prefix",
                "fields": city_fields,
            }
        },
        aggs={"unique_cities": {"terms": {"field": "city_keyword", "size": limit}}},
    )
    locations = [b["key"] for b in city_resp["aggregations"]["unique_cities"]["buckets"]]

    # Hotels by title OR address
    hotel_resp = await es.search(
        index=INDEX,
        size=limit,
        query={
            "bool": {
                "should": [
                    {
                        "multi_match": {
                            "query": q,
                            "type": "bool_prefix",
                            "fields": title_fields,
                        }
                    },
                    {
                        "match": {
                            "address": {
                                "query": q,
                                "fuzziness": "AUTO",
                            }
                        }
                    },
                ],
                "minimum_should_match": 1,
            }
        },
    )
    hotels = [
        {
            "title": h["_source"]["title"],
            "city": h["_source"]["city"],
            "address": h["_source"].get("address") or None,
        }
        for h in hotel_resp["hits"]["hits"]
    ]

    return {"locations": locations, "hotels": hotels}
