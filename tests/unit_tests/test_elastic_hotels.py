"""Unit tests for elastic/hotels.py."""

from unittest.mock import AsyncMock

import pytest

from src.elastic.hotels import (
    ensure_index,
    reindex_all,
    index_hotel,
    remove_hotel,
    autocomplete,
    INDEX,
)


@pytest.fixture
def es():
    return AsyncMock()


async def test_ensure_index_creates(es):
    es.indices.exists.return_value = False
    await ensure_index(es)
    es.indices.create.assert_called_once()


async def test_ensure_index_already_exists(es):
    es.indices.exists.return_value = True
    await ensure_index(es)
    es.indices.create.assert_not_called()


async def test_reindex_all_empty(es):
    es.indices.exists.return_value = True
    await reindex_all(es, [])
    es.bulk.assert_not_called()


async def test_reindex_all_with_hotels(es):
    es.indices.exists.return_value = True
    hotels = [
        {"id": 1, "title": "Hotel A", "city": "Moscow", "address": "Street 1"},
        {"id": 2, "title": "Hotel B", "city": "SPB", "address": None},
    ]
    await reindex_all(es, hotels)
    es.bulk.assert_called_once()
    ops = es.bulk.call_args[1]["operations"]
    # 2 hotels * 2 entries each (action + doc) = 4
    assert len(ops) == 4


async def test_index_hotel(es):
    es.indices.exists.return_value = True
    await index_hotel(es, hotel_id=1, title="Test", city="Moscow", address="Addr")
    es.index.assert_called_once()
    doc = es.index.call_args[1]["document"]
    assert doc["id"] == 1
    assert doc["title"] == "Test"
    assert doc["city_keyword"] == "Moscow"


async def test_index_hotel_no_address(es):
    es.indices.exists.return_value = True
    await index_hotel(es, hotel_id=1, title="Test", city="Moscow", address=None)
    doc = es.index.call_args[1]["document"]
    assert doc["address"] == ""


async def test_remove_hotel(es):
    await remove_hotel(es, hotel_id=42)
    es.delete.assert_called_once_with(index=INDEX, id="42")


async def test_remove_hotel_not_found(es):
    from elasticsearch import NotFoundError

    es.delete.side_effect = NotFoundError(404, "not found", {})
    await remove_hotel(es, hotel_id=42)  # should not raise


async def test_autocomplete(es):
    es.search.side_effect = [
        # City aggregation response
        {"aggregations": {"unique_cities": {"buckets": [{"key": "Moscow"}, {"key": "SPB"}]}}},
        # Hotel search response
        {
            "hits": {
                "hits": [
                    {
                        "_source": {
                            "title": "Grand Hotel",
                            "city": "Moscow",
                            "address": "Red Square 1",
                        }
                    }
                ]
            }
        },
    ]
    result = await autocomplete(es, "Mos", limit=5)
    assert result["locations"] == ["Moscow", "SPB"]
    assert len(result["hotels"]) == 1
    assert result["hotels"][0]["title"] == "Grand Hotel"


async def test_autocomplete_no_results(es):
    es.search.side_effect = [
        {"aggregations": {"unique_cities": {"buckets": []}}},
        {"hits": {"hits": []}},
    ]
    result = await autocomplete(es, "xyz")
    assert result["locations"] == []
    assert result["hotels"] == []
