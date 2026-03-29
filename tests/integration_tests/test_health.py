from httpx import AsyncClient


async def test_health_ok(ac: AsyncClient):
    response = await ac.get("/api/v1/health")
    assert response.status_code in (200, 503)
    data = response.json()
    assert "status" in data
    assert "db" in data
    assert "redis" in data
    assert isinstance(data.get("version"), str) and data["version"]
    assert data["status"] in ("ok", "degraded")


async def test_health_db_reachable(ac: AsyncClient):
    """В тестовой среде БД всегда доступна."""
    response = await ac.get("/api/v1/health")
    assert response.json()["db"] is True


async def test_liveness_always_ok(ac: AsyncClient):
    """Liveness probe всегда возвращает 200 независимо от состояния зависимостей."""
    response = await ac.get("/api/v1/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "live"
    assert isinstance(data.get("version"), str) and data["version"]
