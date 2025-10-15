import io
import uuid
from pathlib import Path
from typing import Dict
from fastapi import UploadFile, HTTPException, status
from PIL import Image, UnidentifiedImageError, ImageFile

from src.services.base import BaseService
from src.tasks.tasks import resize_image

# Разрешаем Pillow читать "truncated" изображения аккуратно
ImageFile.LOAD_TRUNCATED_IMAGES = False

# Конфигурация (при желании вынеси в src.config.settings)
MAX_IMAGE_SIZE = 5_242_880  # 5 MB в байтах
MAX_IMAGE_SIZE_MB = MAX_IMAGE_SIZE / (1024 * 1024)
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_EXTENSIONS = {"jpeg", "jpg", "png", "webp"}
IMAGES_DIR = Path("src/static/images")


class ImagesService(BaseService):
    async def upload_image(self, file: UploadFile) -> Dict:
        """
        Валидирует и сохраняет изображение в файл, запускает Celery-задачу resize_image.
        Возвращает метаданные, пригодные для записи в БД.
        """
        # 1) Быстрая проверка MIME (если предоставлен)
        content_type = (file.content_type or "").lower()
        if content_type and content_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"Неподдерживаемый тип файла: {content_type}",
            )

        # 2) Читаем содержимое (в памяти — OK до MAX_IMAGE_SIZE)
        contents = await file.read()
        file_size = len(contents)
        if file_size == 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Файл пустой")
        if file_size > MAX_IMAGE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Файл слишком большой. Максимальный размер файла: {MAX_IMAGE_SIZE_MB:.2f} МБ",
            )

        # 3) Проверка, что это изображение (Pillow)
        try:
            bio = io.BytesIO(contents)
            # validate by opening and verifying
            img = Image.open(bio)
            img.verify()  # проверяет целостность формата
        except UnidentifiedImageError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Файл не является изображением"
            )
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Повреждённый или неверный файл изображения",
            )

        # 4) Получаем метаданные (повторно открываем, т.к. verify() может менять состояние)
        bio.seek(0)
        try:
            with Image.open(bio) as img_meta:
                img_meta = img_meta.convert("RGBA") if img_meta.mode == "P" else img_meta
                img_format = (img_meta.format or "").lower()
                width, height = img_meta.size
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Не удалось получить метаданные изображения",
            )

        # 5) Нормализация расширения
        ext = img_format
        if ext == "jpeg":
            ext = "jpg"
        if not ext or ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"Неподдерживаемый формат изображения: {img_format}",
            )

        # 6) Подготовка безопасного имени и сохранение
        IMAGES_DIR.mkdir(parents=True, exist_ok=True)
        safe_name = f"{uuid.uuid4().hex}.{ext}"
        image_path = IMAGES_DIR / safe_name

        try:
            # Пишем байты напрямую (атомарность на уровне простая — можно улучшить через tmp + rename)
            with open(image_path, "wb") as f:
                f.write(contents)
        except Exception:
            # В проде логируем полную ошибку
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Не удалось сохранить файл",
            )

        # 7) Запускаем Celery задачу для создания resized-версий
        try:
            # .delay — асинхронно поставить задачу в очередь
            resize_image.delay(str(image_path))
        except Exception:
            # Если Celery недоступен — можно логировать и/или удалить сохранённый файл
            # но не ломаем основной поток загрузки: возвращаем как есть, и сообщаем о warning
            # В проде: логировать
            pass

        # 8) Возвращаем метаданные (удобно хранить в БД)
        return {
            "filename": safe_name,
            "path": str(image_path),
            "content_type": content_type or f"image/{ext}",
            "size": file_size,
            "width": width,
            "height": height,
        }
