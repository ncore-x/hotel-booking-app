import logging
import os
import tempfile
from pathlib import Path
from time import sleep
from typing import Sequence
from PIL import Image, UnidentifiedImageError, ImageOps

from src.database import async_session_maker_null_pool
from src.tasks.celery_app import celery_instance
from src.utils.db_manager import DBManager


@celery_instance.task
def test_task():
    sleep(5)
    print("READY")


@celery_instance.task(bind=True, name="resize_image")
def resize_image(self, image_path: str, sizes: Sequence[int] | None = None) -> dict:
    """
    Celery task: создает несколько версий изображения по ширине (px), сохраняя пропорции.
    - image_path: полный путь к исходному файлу
    - sizes: список желаемых ширин в пикселях (по умолчанию [1000, 500, 200])
    Возвращает dict с информацией о сохраненных файлах.
    """
    if sizes is None:
        sizes = [1000, 500, 200]

    output_folder = Path("src/static/images")
    output_folder.mkdir(parents=True, exist_ok=True)

    results = {"original": str(image_path), "generated": []}

    try:
        # Открываем изображение и корректируем ориентацию по EXIF (если есть)
        with Image.open(image_path) as img:
            img = ImageOps.exif_transpose(img)  # исправляет поворот из EXIF
            original_format = img.format or "JPEG"
            original_mode = img.mode
            width, height = img.size
            logging.debug(
                f"resize_image: opened {image_path=} {width=}x{height=} {original_format=} {original_mode=}"
            )

            for size in sizes:
                if size <= 0:
                    logging.warning(f"Пропускаю некорректный размер {size}")
                    continue

                # Вычисляем новую высоту, чтобы сохранить пропорции
                new_width = int(size)
                new_height = int(round(height * (new_width / width)))

                # Клонируем изображение перед изменением
                img_copy = img.copy()
                try:
                    img_resized = img_copy.resize((new_width, new_height), Image.Resampling.LANCZOS)
                finally:
                    img_copy.close()

                base_name = Path(image_path).stem
                # включает точку, e.g. '.jpg'
                ext = Path(image_path).suffix.lower()
                if not ext:
                    ext = f".{(original_format or 'jpg').lower()}"
                new_file_name = f"{base_name}_{new_width}px{ext}"
                output_path = output_folder / new_file_name

                # Обработка альфа-канала при сохранении в JPEG
                save_kwargs = {}
                if ext in (".jpg", ".jpeg") or original_format.upper() == "JPEG":
                    if img_resized.mode in ("RGBA", "LA") or (
                        img_resized.mode == "P" and "transparency" in img_resized.info
                    ):
                        background = Image.new("RGB", img_resized.size, (255, 255, 255))
                        background.paste(img_resized, mask=img_resized.split()[-1])
                        img_to_save = background
                    else:
                        img_to_save = img_resized.convert("RGB")
                    save_kwargs.update({"format": "JPEG", "quality": 85, "optimize": True})
                else:
                    img_to_save = img_resized
                    save_kwargs.update({"optimize": True})

                # Запись через временный файл, затем атомарный переезд
                tmp_name = None
                try:
                    with tempfile.NamedTemporaryFile(delete=False, dir=str(output_folder)) as tmp:
                        tmp_name = tmp.name
                    img_to_save.save(tmp_name, **save_kwargs)
                    # атомарно заменяет целевой файл
                    os.replace(tmp_name, str(output_path))
                    results["generated"].append(
                        {
                            "size": new_width,
                            "path": str(output_path),
                            "width": new_width,
                            "height": new_height,
                        }
                    )
                    logging.info(f"Saved resized image: {output_path} ({new_width}x{new_height})")
                except Exception as exc:
                    logging.exception(f"Не удалось сохранить resized image to {output_path}: {exc}")
                    try:
                        if tmp_name and os.path.exists(tmp_name):
                            os.remove(tmp_name)
                    except Exception:
                        pass
                finally:
                    try:
                        img_resized.close()
                    except Exception:
                        pass
                    try:
                        if img_to_save is not img_resized:
                            img_to_save.close()
                    except Exception:
                        pass

    except UnidentifiedImageError:
        logging.exception(f"Файл не является изображением: {image_path}")
        raise
    except FileNotFoundError:
        logging.exception(f"Исходный файл не найден: {image_path}")
        raise
    except Exception as e:
        logging.exception(f"Ошибка при ресайзе изображения {image_path}: {e}")
        raise

    return results


async def get_bookings_with_today_checkin_helper():
    async with DBManager(session_factory=async_session_maker_null_pool) as db:
        bookings = await db.bookings.get_bookings_with_today_checkin()
        logging.debug(f"{bookings=}")


@celery_instance.task(name="booking_today_checkin")
def send_emails_to_users_with_today_checkin():
    import asyncio

    asyncio.run(get_bookings_with_today_checkin_helper())
