import pytest
from httpx import AsyncClient

from src.config import settings


def _auth_headers() -> dict:
    if settings.METRICS_TOKEN:
        return {"Authorization": f"Bearer {settings.METRICS_TOKEN}"}
    return {}


async def test_metrics_returns_200(ac: AsyncClient):
    if not settings.METRICS_ENABLED:
        pytest.skip("METRICS_ENABLED=False")
    response = await ac.get("/metrics", headers=_auth_headers())
    assert response.status_code == 200


async def test_metrics_content_type(ac: AsyncClient):
    if not settings.METRICS_ENABLED:
        pytest.skip("METRICS_ENABLED=False")
    response = await ac.get("/metrics", headers=_auth_headers())
    assert "text/plain" in response.headers["content-type"]


async def test_metrics_contains_fastapi_metrics(ac: AsyncClient):
    if not settings.METRICS_ENABLED:
        pytest.skip("METRICS_ENABLED=False")
    await ac.get("/api/v1/health")  # generate traffic
    response = await ac.get("/metrics", headers=_auth_headers())
    body = response.text
    assert "fastapi_requests_total" in body
    assert "fastapi_responses_total" in body
    assert "fastapi_requests_in_progress" in body
    assert "fastapi_requests_duration_seconds" in body
    assert "fastapi_exceptions_total" in body


async def test_metrics_app_name_label(ac: AsyncClient):
    if not settings.METRICS_ENABLED:
        pytest.skip("METRICS_ENABLED=False")
    await ac.get("/api/v1/health")
    response = await ac.get("/metrics", headers=_auth_headers())
    assert 'app_name="hotel_booking"' in response.text


async def test_metrics_requires_auth_when_token_set(ac: AsyncClient):
    """Без токена /metrics возвращает 401, если METRICS_TOKEN задан."""
    if not settings.METRICS_ENABLED:
        pytest.skip("METRICS_ENABLED=False")
    if not settings.METRICS_TOKEN:
        pytest.skip("METRICS_TOKEN not set")
    response = await ac.get("/metrics")
    assert response.status_code == 401


async def test_metrics_not_under_api_prefix(ac: AsyncClient):
    """Prometheus endpoint не должен быть под /api/v1."""
    if not settings.METRICS_ENABLED:
        pytest.skip("METRICS_ENABLED=False")
    ok = await ac.get("/metrics", headers=_auth_headers())
    not_found = await ac.get("/api/v1/metrics")
    assert ok.status_code == 200
    assert not_found.status_code == 404
