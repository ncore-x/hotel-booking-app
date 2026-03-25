from httpx import AsyncClient


async def test_health_ok(ac: AsyncClient):
    response = await ac.get("/api/v1/health")
    assert response.status_code in (200, 503)
    data = response.json()
    assert "status" in data
    assert "db" in data
    assert "redis" in data
    assert data["status"] in ("ok", "degraded")


async def test_health_db_reachable(ac: AsyncClient):
    """В тестовой среде БД всегда доступна."""
    response = await ac.get("/api/v1/health")
    assert response.json()["db"] is True
