"""
Тесты загрузки изображений отелей: POST/GET /hotels/{hotel_id}/images.
"""
import io

from httpx import AsyncClient


def _make_png_bytes() -> bytes:
    """Минимальный валидный PNG (1x1 пиксель)."""
    import struct, zlib

    def chunk(name: bytes, data: bytes) -> bytes:
        c = name + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)

    signature = b"\x89PNG\r\n\x1a\n"
    ihdr = chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
    idat = chunk(b"IDAT", zlib.compress(b"\x00\xFF\xFF\xFF"))
    iend = chunk(b"IEND", b"")
    return signature + ihdr + idat + iend


_PNG = _make_png_bytes()


# ──── GET /hotels/{hotel_id}/images ──────────────────────────────────────────

async def test_get_hotel_images_empty(ac: AsyncClient):
    """Hotel без загруженных изображений возвращает пустой список."""
    response = await ac.get("/api/v1/hotels/1/images")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


async def test_get_hotel_images_not_found(ac: AsyncClient):
    response = await ac.get("/api/v1/hotels/999999/images")
    assert response.status_code == 404


# ──── POST /hotels/{hotel_id}/images ─────────────────────────────────────────

async def test_upload_image_forbidden_for_regular_user(authenticated_ac: AsyncClient):
    response = await authenticated_ac.post(
        "/api/v1/hotels/1/images",
        files={"file": ("test.png", io.BytesIO(_PNG), "image/png")},
    )
    assert response.status_code == 403


async def test_upload_image_unauthenticated(unauth_ac: AsyncClient):
    response = await unauth_ac.post(
        "/api/v1/hotels/1/images",
        files={"file": ("test.png", io.BytesIO(_PNG), "image/png")},
    )
    assert response.status_code == 401


async def test_upload_image_hotel_not_found(admin_ac: AsyncClient):
    response = await admin_ac.post(
        "/api/v1/hotels/999999/images",
        files={"file": ("test.png", io.BytesIO(_PNG), "image/png")},
    )
    assert response.status_code == 404


async def test_upload_image_success(admin_ac: AsyncClient):
    response = await admin_ac.post(
        "/api/v1/hotels/1/images",
        files={"file": ("test.png", io.BytesIO(_PNG), "image/png")},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["hotel_id"] == 1
    assert "filename" in data
    assert "id" in data
    assert data["content_type"] == "image/png"


async def test_uploaded_image_appears_in_list(admin_ac: AsyncClient, ac: AsyncClient):
    """После загрузки изображение видно в GET /hotels/{hotel_id}/images."""
    await admin_ac.post(
        "/api/v1/hotels/1/images",
        files={"file": ("listed.png", io.BytesIO(_PNG), "image/png")},
    )
    response = await ac.get("/api/v1/hotels/1/images")
    assert response.status_code == 200
    images = response.json()
    assert len(images) >= 1
    assert all("filename" in img and "hotel_id" in img for img in images)


async def test_upload_image_empty_file(admin_ac: AsyncClient):
    response = await admin_ac.post(
        "/api/v1/hotels/1/images",
        files={"file": ("empty.png", io.BytesIO(b""), "image/png")},
    )
    assert response.status_code == 400


async def test_upload_image_unsupported_type(admin_ac: AsyncClient):
    response = await admin_ac.post(
        "/api/v1/hotels/1/images",
        files={"file": ("doc.pdf", io.BytesIO(b"%PDF-1.4"), "application/pdf")},
    )
    assert response.status_code == 415
