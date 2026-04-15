import logging
import os
import tempfile
from pathlib import Path
from typing import Sequence
from PIL import Image, UnidentifiedImageError, ImageOps

from src.database import async_session_maker_null_pool
from src.tasks.celery_app import celery_instance
from src.utils.db_manager import DBManager


@celery_instance.task(
    bind=True,
    name="resize_image",
    autoretry_for=(Exception,),
    max_retries=3,
    default_retry_delay=60,
)
def resize_image(self, image_path: str, sizes: Sequence[int] | None = None) -> dict:
    """
    Celery task: создает несколько версий изображения по ширине (px), сохраняя пропорции.
    - image_path: полный путь к исходному файлу
    - sizes: список желаемых ширин в пикселях (по умолчанию [1000, 500, 200])
    Возвращает dict с информацией о сохраненных файлах.
    """
    if sizes is None:
        sizes = [1000, 500, 200]

    from src.config import settings

    output_folder = settings.IMAGES_DIR
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


def _build_checkin_email(booking_id: int, date_from, date_to) -> tuple[str, str, str]:
    """Возвращает (subject, plain_text, html) для письма о заезде."""
    subject = f"Напоминание о заезде — бронирование #{booking_id}"
    plain = (
        f"Здравствуйте!\n\n"
        f"Напоминаем, что сегодня, {date_from}, начинается ваше бронирование #{booking_id}.\n"
        f"Дата выезда: {date_to}.\n\n"
        f"Хорошего отдыха!\n"
        f"Команда Hotel Booking"
    )
    html = f"""<!DOCTYPE html>
<html lang="ru">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f4f4f4;font-family:Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f4;padding:32px 0;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:8px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,.08);">
        <tr>
          <td style="background:#2563eb;padding:28px 40px;">
            <h1 style="margin:0;color:#ffffff;font-size:22px;font-weight:700;">Hotel Booking</h1>
          </td>
        </tr>
        <tr>
          <td style="padding:36px 40px;">
            <h2 style="margin:0 0 16px;color:#1e293b;font-size:20px;">Сегодня день заезда!</h2>
            <p style="margin:0 0 12px;color:#475569;font-size:15px;line-height:1.6;">
              Напоминаем, что сегодня <strong>{date_from}</strong> начинается ваше бронирование
              <strong>#{booking_id}</strong>.
            </p>
            <p style="margin:0 0 28px;color:#475569;font-size:15px;line-height:1.6;">
              Дата выезда: <strong>{date_to}</strong>.
            </p>
            <table cellpadding="0" cellspacing="0">
              <tr>
                <td style="background:#2563eb;border-radius:6px;padding:12px 28px;">
                  <span style="color:#ffffff;font-size:15px;font-weight:600;text-decoration:none;">
                    Бронирование #{booking_id}
                  </span>
                </td>
              </tr>
            </table>
          </td>
        </tr>
        <tr>
          <td style="background:#f8fafc;padding:20px 40px;border-top:1px solid #e2e8f0;">
            <p style="margin:0;color:#94a3b8;font-size:13px;">
              Хорошего отдыха! &mdash; Команда Hotel Booking
            </p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""
    return subject, plain, html


def _send_checkin_email(to_email: str, booking_id: int, date_from, date_to) -> None:
    """
    Отправляет письмо о заезде через SMTP.
    Если SMTP не настроен — пропускает отправку и логирует предупреждение.
    """
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from src.config import settings

    if not settings.SMTP_HOST:
        logging.warning(
            f"SMTP не настроен — письмо о заезде не отправлено "
            f"(booking_id={booking_id}, to={to_email})"
        )
        return

    subject, plain, html = _build_checkin_email(booking_id, date_from, date_to)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_FROM
    msg["To"] = to_email
    msg.attach(MIMEText(plain, "plain", "utf-8"))
    msg.attach(MIMEText(html, "html", "utf-8"))

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as smtp:
        smtp.ehlo()
        smtp.starttls()
        if settings.SMTP_USER and settings.SMTP_PASSWORD:
            smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        smtp.sendmail(settings.SMTP_FROM, [to_email], msg.as_string())
    logging.info(f"Письмо о заезде отправлено: booking_id={booking_id}, to={to_email}")


@celery_instance.task(
    name="send_checkin_email",
    autoretry_for=(Exception,),
    max_retries=3,
    default_retry_delay=60,
)
def send_checkin_email_task(
    to_email: str, booking_id: int, date_from_str: str, date_to_str: str
) -> None:
    """Celery task: отправляет одно письмо о заезде в изолированном воркере."""
    from datetime import date

    _send_checkin_email(
        to_email=to_email,
        booking_id=booking_id,
        date_from=date.fromisoformat(date_from_str),
        date_to=date.fromisoformat(date_to_str),
    )


def _send_confirmation_email(to_email: str, subject: str, confirm_url: str) -> None:
    """
    Отправляет письмо с ссылкой подтверждения через SMTP.
    Если SMTP не настроен — логирует ссылку и продолжает.
    """
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from src.config import settings

    plain = (
        f"Здравствуйте!\n\n"
        f"Для подтверждения перейдите по ссылке:\n{confirm_url}\n\n"
        f"Ссылка действительна 1 час. Если вы не запрашивали изменение — проигнорируйте письмо.\n\n"
        f"С уважением,\nКоманда Hotel Booking"
    )
    html = f"""<!DOCTYPE html>
<html lang="ru">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f4f4f4;font-family:Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f4;padding:32px 0;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:8px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,.08);">
        <tr>
          <td style="background:#2563eb;padding:28px 40px;">
            <h1 style="margin:0;color:#ffffff;font-size:22px;font-weight:700;">Hotel Booking</h1>
          </td>
        </tr>
        <tr>
          <td style="padding:36px 40px;">
            <h2 style="margin:0 0 16px;color:#1e293b;font-size:20px;">{subject}</h2>
            <p style="margin:0 0 28px;color:#475569;font-size:15px;line-height:1.6;">
              Нажмите кнопку ниже для подтверждения. Ссылка действительна&nbsp;<strong>1&nbsp;час</strong>.
            </p>
            <table cellpadding="0" cellspacing="0">
              <tr>
                <td style="background:#2563eb;border-radius:6px;">
                  <a href="{confirm_url}" style="display:inline-block;padding:12px 28px;color:#ffffff;font-size:15px;font-weight:600;text-decoration:none;">
                    Подтвердить
                  </a>
                </td>
              </tr>
            </table>
            <p style="margin:24px 0 0;color:#94a3b8;font-size:13px;">
              Если кнопка не работает, скопируйте ссылку в браузер:<br>
              <a href="{confirm_url}" style="color:#2563eb;word-break:break-all;">{confirm_url}</a>
            </p>
          </td>
        </tr>
        <tr>
          <td style="background:#f8fafc;padding:20px 40px;border-top:1px solid #e2e8f0;">
            <p style="margin:0;color:#94a3b8;font-size:13px;">
              Если вы не запрашивали это изменение — просто проигнорируйте письмо.
            </p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""

    if not settings.SMTP_HOST:
        logging.warning(
            "SMTP не настроен — письмо подтверждения не отправлено. Ссылка для разработки: %s",
            confirm_url,
        )
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_FROM
    msg["To"] = to_email
    msg.attach(MIMEText(plain, "plain", "utf-8"))
    msg.attach(MIMEText(html, "html", "utf-8"))

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as smtp:
        smtp.ehlo()
        smtp.starttls()
        if settings.SMTP_USER and settings.SMTP_PASSWORD:
            smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        smtp.sendmail(settings.SMTP_FROM, [to_email], msg.as_string())
    logging.info("Письмо подтверждения отправлено: to=%s, subject=%s", to_email, subject)


@celery_instance.task(
    name="send_confirmation_email",
    autoretry_for=(Exception,),
    max_retries=3,
    default_retry_delay=60,
)
def send_confirmation_email_task(to_email: str, subject: str, confirm_url: str) -> None:
    """Celery task: отправляет письмо с ссылкой подтверждения."""
    _send_confirmation_email(to_email=to_email, subject=subject, confirm_url=confirm_url)


async def _get_bookings_and_notify():
    async with DBManager(session_factory=async_session_maker_null_pool) as db:
        rows = await db.bookings.get_today_checkins_with_emails()
        logging.info(f"Заезды сегодня: {len(rows)} бронирований")
        for row in rows:
            try:
                booking = row["booking"]
                send_checkin_email_task.delay(
                    to_email=row["email"],
                    booking_id=booking.id,
                    date_from_str=str(booking.date_from),
                    date_to_str=str(booking.date_to),
                )
            except Exception as e:
                logging.error(f"Ошибка обработки бронирования {row['booking'].id}: {e}")


@celery_instance.task(name="booking_today_checkin")
def send_emails_to_users_with_today_checkin():
    import asyncio

    asyncio.run(_get_bookings_and_notify())
