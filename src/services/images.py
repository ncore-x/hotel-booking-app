import io
import uuid

from fastapi import UploadFile
from PIL import Image, UnidentifiedImageError, ImageFile

from src.config import settings
from src.exceptions import (
    EmptyFileException,
    FileTooLargeException,
    HotelNotFoundException,
    ObjectNotFoundException,
    UnsupportedMediaTypeException,
    CorruptedImageException,
)
from src.schemas.images import HotelImage, HotelImageAdd, ImageUploadResponse
from src.services.base import BaseService
from src.tasks.tasks import resize_image

ImageFile.LOAD_TRUNCATED_IMAGES = False

ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_EXTENSIONS = {"jpeg", "jpg", "png", "webp"}


class ImagesService(BaseService):
    async def upload_image(
        self, hotel_id: int, file: UploadFile
    ) -> ImageUploadResponse:
        # Verify hotel exists
        try:
            await self.db.hotels.get_one(id=hotel_id)
        except ObjectNotFoundException as ex:
            raise HotelNotFoundException from ex

        content_type = (file.content_type or "").lower()
        if content_type and content_type not in ALLOWED_MIME_TYPES:
            raise UnsupportedMediaTypeException(
                f"Неподдерживаемый тип файла: {content_type}"
            )

        contents = await file.read()
        if len(contents) == 0:
            raise EmptyFileException()

        if len(contents) > settings.MAX_IMAGE_SIZE_BYTES:
            max_mb = settings.MAX_IMAGE_SIZE_BYTES / (1024 * 1024)
            raise FileTooLargeException(
                f"Файл слишком большой. Максимальный размер: {max_mb:.0f} МБ"
            )

        bio = io.BytesIO(contents)
        try:
            img = Image.open(bio)
            img.verify()
        except UnidentifiedImageError:
            raise CorruptedImageException("Файл не является изображением")
        except Exception:
            raise CorruptedImageException()

        bio.seek(0)
        try:
            with Image.open(bio) as img_meta:
                img_meta = (
                    img_meta.convert("RGBA") if img_meta.mode == "P" else img_meta
                )
                img_format = (img_meta.format or "").lower()
                width, height = img_meta.size
        except Exception:
            raise CorruptedImageException("Не удалось получить метаданные изображения")

        ext = "jpg" if img_format == "jpeg" else img_format
        if not ext or ext not in ALLOWED_EXTENSIONS:
            raise UnsupportedMediaTypeException(
                f"Неподдерживаемый формат изображения: {img_format}"
            )

        images_dir = settings.IMAGES_DIR
        images_dir.mkdir(parents=True, exist_ok=True)
        safe_name = f"{uuid.uuid4().hex}.{ext}"
        image_path = images_dir / safe_name

        try:
            with open(image_path, "wb") as f:
                f.write(contents)
        except Exception as e:
            raise CorruptedImageException(f"Не удалось сохранить файл: {e}")

        final_content_type = content_type or f"image/{ext}"

        # Save record to DB
        record = await self.db.hotel_images.add(
            HotelImageAdd(
                hotel_id=hotel_id, filename=safe_name, content_type=final_content_type
            )
        )
        await self.db.commit()

        try:
            resize_image.delay(str(image_path))
        except Exception:
            pass  # Celery недоступен — не критично

        return ImageUploadResponse(
            id=record.id,
            hotel_id=hotel_id,
            filename=safe_name,
            content_type=final_content_type,
            size=len(contents),
            width=width,
            height=height,
        )

    async def get_hotel_images(self, hotel_id: int) -> list[HotelImage]:
        try:
            await self.db.hotels.get_one(id=hotel_id)
        except ObjectNotFoundException as ex:
            raise HotelNotFoundException from ex
        return await self.db.hotel_images.get_filtered(hotel_id=hotel_id)
