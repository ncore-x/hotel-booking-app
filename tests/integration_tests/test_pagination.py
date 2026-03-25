"""
Тесты логики пагинации: has_prev/has_next, страницы, per_page.
"""
from datetime import date, timedelta

from httpx import AsyncClient


def future(days: int) -> str:
    return (date.today() + timedelta(days=days)).isoformat()


_DATE_FROM = future(30)
_DATE_TO = future(45)


# ──── PaginatedResponse — общая логика ───────────────────────────────────────

async def test_first_page_has_no_prev(ac: AsyncClient):
    r = await ac.get("/api/v1/hotels", params={"date_from": _DATE_FROM, "date_to": _DATE_TO, "page": 1, "per_page": 1})
    assert r.status_code == 200
    assert r.json()["has_prev"] is False


async def test_second_page_has_prev(ac: AsyncClient):
    # Убеждаемся что отелей >= 2 (в mock_hotels.json их 3)
    r = await ac.get("/api/v1/hotels", params={"date_from": _DATE_FROM, "date_to": _DATE_TO, "page": 2, "per_page": 1})
    assert r.status_code == 200
    assert r.json()["has_prev"] is True


async def test_last_page_has_no_next(ac: AsyncClient):
    # Получаем все за одну страницу
    r_all = await ac.get("/api/v1/hotels", params={"date_from": _DATE_FROM, "date_to": _DATE_TO, "per_page": 100})
    total = r_all.json()["total"]
    # Запрашиваем последнюю страницу
    r = await ac.get(
        "/api/v1/hotels",
        params={"date_from": _DATE_FROM, "date_to": _DATE_TO, "page": r_all.json()["pages"], "per_page": 100},
    )
    assert r.status_code == 200
    assert r.json()["has_next"] is False


async def test_pages_calculation(ac: AsyncClient):
    r = await ac.get("/api/v1/hotels", params={"date_from": _DATE_FROM, "date_to": _DATE_TO, "per_page": 1})
    data = r.json()
    import math
    expected_pages = max(1, math.ceil(data["total"] / data["per_page"]))
    assert data["pages"] == expected_pages


async def test_total_consistent_across_pages(ac: AsyncClient):
    """total должен быть одинаковым на всех страницах."""
    r1 = await ac.get("/api/v1/hotels", params={"date_from": _DATE_FROM, "date_to": _DATE_TO, "page": 1, "per_page": 1})
    r2 = await ac.get("/api/v1/hotels", params={"date_from": _DATE_FROM, "date_to": _DATE_TO, "page": 2, "per_page": 1})
    # Обе страницы могут вернуть 404 если нет второй, но total совпадает
    if r2.status_code == 200:
        assert r1.json()["total"] == r2.json()["total"]


async def test_facilities_pagination(ac: AsyncClient):
    r = await ac.get("/api/v1/facilities", params={"page": 1, "per_page": 5})
    assert r.status_code == 200
    data = r.json()
    assert len(data["items"]) <= 5
    assert data["per_page"] == 5
    assert "has_next" in data
    assert "has_prev" in data


async def test_rooms_pagination(ac: AsyncClient):
    r = await ac.get(
        "/api/v1/hotels/1/rooms",
        params={"date_from": _DATE_FROM, "date_to": _DATE_TO, "per_page": 1, "page": 1},
    )
    assert r.status_code == 200
    data = r.json()
    assert "items" in data
    assert "total" in data
    assert "has_prev" in data
    assert len(data["items"]) <= 1
