import pytest
from httpx import AsyncClient


# ──── JSONErrorHandlerMiddleware ──────────────────────────────────────────────

@pytest.mark.parametrize(
    "body, expected_fragment",
    [
        (b"{bad json", "JSON"),
        (b'{"key": }', "JSON"),
        (b'"unterminated', "JSON"),
    ],
)
async def test_invalid_json_returns_422(ac: AsyncClient, body: bytes, expected_fragment: str):
    response = await ac.post(
        "/api/v1/auth/register",
        content=body,
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 422
    assert expected_fragment in response.text


async def test_valid_json_passes_through(ac: AsyncClient):
    """Валидный JSON не должен перехватываться middleware."""
    response = await ac.post(
        "/api/v1/auth/register",
        json={"email": "valid@json.com", "password": "ValidPass1"},
    )
    # 201 или 409 — значит middleware не сломал запрос
    assert response.status_code in (201, 409)


# ──── RequestIDMiddleware ─────────────────────────────────────────────────────

async def test_request_id_generated_when_absent(ac: AsyncClient):
    response = await ac.get("/api/v1/facilities")
    assert "x-request-id" in response.headers
    assert len(response.headers["x-request-id"]) == 36  # UUID4 format


async def test_request_id_echoed_from_client(ac: AsyncClient):
    custom_id = "test-123-abc"
    response = await ac.get(
        "/api/v1/facilities",
        headers={"X-Request-ID": custom_id},
    )
    assert response.headers["x-request-id"] == custom_id


async def test_request_id_unique_per_request(ac: AsyncClient):
    r1 = await ac.get("/api/v1/facilities")
    r2 = await ac.get("/api/v1/facilities")
    assert r1.headers["x-request-id"] != r2.headers["x-request-id"]
