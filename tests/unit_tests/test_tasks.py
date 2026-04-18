"""Unit tests for Celery tasks."""

import os
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from PIL import Image

from src.tasks.tasks import (
    _build_checkin_email,
    _send_checkin_email,
    _send_confirmation_email,
)


@pytest.fixture
def sample_image(tmp_path):
    """Create a real test image file."""
    img = Image.new("RGB", (2000, 1000), color="red")
    path = tmp_path / "test_image.jpg"
    img.save(str(path), format="JPEG")
    img.close()
    return str(path)


@pytest.fixture
def sample_png_rgba(tmp_path):
    """Create a RGBA PNG for alpha channel testing."""
    img = Image.new("RGBA", (2000, 1000), color=(255, 0, 0, 128))
    path = tmp_path / "test_rgba.png"
    img.save(str(path), format="PNG")
    img.close()
    return str(path)


def _call_resize(image_path, sizes=None):
    """Call the underlying resize_image function bypassing Celery decorator."""
    from src.tasks.tasks import resize_image

    # _orig_run is the original function before autoretry wrapping;
    # bind=True means first arg is 'self' (the task instance)
    if sizes is not None:
        return resize_image._orig_run(image_path, sizes)
    return resize_image._orig_run(image_path)


def test_resize_image_default_sizes(sample_image, tmp_path):
    with patch("src.config.settings") as mock_settings:
        mock_settings.IMAGES_DIR = tmp_path / "output"
        result = _call_resize(sample_image)

    assert result["original"] == sample_image
    assert len(result["generated"]) == 3
    widths = [g["width"] for g in result["generated"]]
    assert set(widths) == {1000, 500, 200}


def test_resize_image_custom_sizes(sample_image, tmp_path):
    with patch("src.config.settings") as mock_settings:
        mock_settings.IMAGES_DIR = tmp_path / "output"
        result = _call_resize(sample_image, sizes=[800])

    assert len(result["generated"]) == 1
    assert result["generated"][0]["width"] == 800


def test_resize_image_skips_invalid_size(sample_image, tmp_path):
    with patch("src.config.settings") as mock_settings:
        mock_settings.IMAGES_DIR = tmp_path / "output"
        result = _call_resize(sample_image, sizes=[0, -1, 500])

    assert len(result["generated"]) == 1
    assert result["generated"][0]["width"] == 500


def test_resize_image_file_not_found():
    with (
        patch("src.config.settings") as mock_settings,
        pytest.raises(FileNotFoundError),
    ):
        mock_settings.IMAGES_DIR = Path("/tmp/output")
        _call_resize("/nonexistent/path.jpg")


def test_resize_image_not_an_image(tmp_path):
    from PIL import UnidentifiedImageError

    fake_file = tmp_path / "not_image.jpg"
    fake_file.write_text("not an image")

    with (
        patch("src.config.settings") as mock_settings,
        pytest.raises(UnidentifiedImageError),
    ):
        mock_settings.IMAGES_DIR = tmp_path / "output"
        _call_resize(str(fake_file))


def test_resize_image_preserves_aspect_ratio(sample_image, tmp_path):
    with patch("src.config.settings") as mock_settings:
        mock_settings.IMAGES_DIR = tmp_path / "output"
        result = _call_resize(sample_image, sizes=[1000])

    gen = result["generated"][0]
    # Original is 2000x1000, so 1000px wide should be 500px tall
    assert gen["width"] == 1000
    assert gen["height"] == 500


def test_resize_rgba_to_jpeg(sample_png_rgba, tmp_path):
    """RGBA images saved as JPEG should get white background."""
    # Rename to .jpg so it triggers JPEG save path
    jpg_path = tmp_path / "test_rgba.jpg"
    os.rename(sample_png_rgba, str(jpg_path))

    with patch("src.config.settings") as mock_settings:
        mock_settings.IMAGES_DIR = tmp_path / "output"
        result = _call_resize(str(jpg_path), sizes=[500])

    assert len(result["generated"]) == 1
    output_path = result["generated"][0]["path"]
    assert os.path.exists(output_path)


def test_build_checkin_email():
    from datetime import date

    subject, plain, html = _build_checkin_email(42, date(2026, 4, 10), date(2026, 4, 15))
    assert "42" in subject
    assert "2026-04-10" in plain
    assert "2026-04-15" in plain
    assert "42" in html
    assert "html" in html.lower()


def test_send_checkin_email_no_smtp():
    from datetime import date

    with patch("src.config.settings") as mock_settings:
        mock_settings.SMTP_HOST = ""
        _send_checkin_email("test@example.com", 1, date(2026, 4, 10), date(2026, 4, 15))
    # Should not raise, just logs warning


def test_send_checkin_email_with_smtp():
    from datetime import date

    with (
        patch("src.config.settings") as mock_settings,
        patch("smtplib.SMTP") as mock_smtp_class,
    ):
        mock_settings.SMTP_HOST = "smtp.example.com"
        mock_settings.SMTP_PORT = 587
        mock_settings.SMTP_FROM = "noreply@example.com"
        mock_settings.SMTP_USER = "user"
        mock_settings.SMTP_PASSWORD = "pass"

        mock_smtp = MagicMock()
        mock_smtp_class.return_value.__enter__ = MagicMock(return_value=mock_smtp)
        mock_smtp_class.return_value.__exit__ = MagicMock(return_value=False)

        _send_checkin_email("guest@example.com", 1, date(2026, 4, 10), date(2026, 4, 15))

        mock_smtp.ehlo.assert_called_once()
        mock_smtp.starttls.assert_called_once()
        mock_smtp.login.assert_called_once_with("user", "pass")
        mock_smtp.sendmail.assert_called_once()


def test_send_checkin_email_no_auth():
    from datetime import date

    with (
        patch("src.config.settings") as mock_settings,
        patch("smtplib.SMTP") as mock_smtp_class,
    ):
        mock_settings.SMTP_HOST = "smtp.example.com"
        mock_settings.SMTP_PORT = 587
        mock_settings.SMTP_FROM = "noreply@example.com"
        mock_settings.SMTP_USER = ""
        mock_settings.SMTP_PASSWORD = ""

        mock_smtp = MagicMock()
        mock_smtp_class.return_value.__enter__ = MagicMock(return_value=mock_smtp)
        mock_smtp_class.return_value.__exit__ = MagicMock(return_value=False)

        _send_checkin_email("guest@example.com", 1, date(2026, 4, 10), date(2026, 4, 15))

        mock_smtp.login.assert_not_called()
        mock_smtp.sendmail.assert_called_once()


def test_send_checkin_email_task():
    """send_checkin_email_task parses ISO date strings and calls _send_checkin_email."""
    from src.tasks.tasks import send_checkin_email_task

    with patch("src.tasks.tasks._send_checkin_email") as mock_send:
        send_checkin_email_task._orig_run(
            to_email="guest@test.com",
            booking_id=42,
            date_from_str="2026-05-01",
            date_to_str="2026-05-05",
        )

    from datetime import date

    mock_send.assert_called_once_with(
        to_email="guest@test.com",
        booking_id=42,
        date_from=date(2026, 5, 1),
        date_to=date(2026, 5, 5),
    )


async def test_get_bookings_and_notify():
    """_get_bookings_and_notify queries DB and dispatches email tasks."""
    from unittest.mock import AsyncMock

    from src.tasks.tasks import _get_bookings_and_notify

    mock_booking1 = MagicMock(id=1, date_from="2026-05-01", date_to="2026-05-05")
    mock_booking2 = MagicMock(id=2, date_from="2026-05-01", date_to="2026-05-03")
    rows = [
        {"booking": mock_booking1, "email": "a@test.com"},
        {"booking": mock_booking2, "email": "b@test.com"},
    ]

    mock_db_inner = AsyncMock()
    mock_db_inner.bookings.get_today_checkins_with_emails.return_value = rows

    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value = mock_db_inner

    with (
        patch("src.tasks.tasks.DBManager", return_value=mock_ctx),
        patch("src.tasks.tasks.send_checkin_email_task") as mock_task,
    ):
        await _get_bookings_and_notify()

    assert mock_task.delay.call_count == 2


def test_send_confirmation_email_no_smtp():
    """Если SMTP_HOST не задан — просто логирует и возвращает без ошибки."""
    with patch("src.config.settings") as mock_settings:
        mock_settings.SMTP_HOST = ""
        _send_confirmation_email(
            to_email="user@example.com",
            subject="Confirm",
            confirm_url="http://localhost/confirm?token=abc",
        )


def test_send_confirmation_email_with_smtp():
    """Успешная отправка вызывает ehlo, starttls, login, sendmail."""
    with (
        patch("src.config.settings") as mock_settings,
        patch("smtplib.SMTP") as mock_smtp_class,
    ):
        mock_settings.SMTP_HOST = "smtp.example.com"
        mock_settings.SMTP_PORT = 587
        mock_settings.SMTP_FROM = "noreply@example.com"
        mock_settings.SMTP_USER = "user"
        mock_settings.SMTP_PASSWORD = "pass"

        mock_smtp = MagicMock()
        mock_smtp_class.return_value.__enter__ = MagicMock(return_value=mock_smtp)
        mock_smtp_class.return_value.__exit__ = MagicMock(return_value=False)

        _send_confirmation_email(
            to_email="user@example.com",
            subject="Подтверждение смены пароля",
            confirm_url="http://localhost/confirm?token=abc",
        )

        mock_smtp.ehlo.assert_called_once()
        mock_smtp.starttls.assert_called_once()
        mock_smtp.login.assert_called_once_with("user", "pass")
        mock_smtp.sendmail.assert_called_once()


def test_send_confirmation_email_smtp_unreachable_does_not_raise():
    """OSError (сеть недоступна) логируется как WARNING, задача не падает."""
    with (
        patch("src.config.settings") as mock_settings,
        patch("smtplib.SMTP") as mock_smtp_class,
    ):
        mock_settings.SMTP_HOST = "smtp.example.com"
        mock_settings.SMTP_PORT = 587
        mock_settings.SMTP_FROM = "noreply@example.com"
        mock_settings.SMTP_USER = ""
        mock_settings.SMTP_PASSWORD = ""
        mock_smtp_class.side_effect = OSError(101, "Network is unreachable")

        _send_confirmation_email(
            to_email="user@example.com",
            subject="Подтверждение",
            confirm_url="http://localhost/confirm?token=xyz",
        )


def test_send_checkin_email_smtp_unreachable_does_not_raise():
    """OSError при отправке письма о заезде логируется, задача не падает."""
    from datetime import date

    with (
        patch("src.config.settings") as mock_settings,
        patch("smtplib.SMTP") as mock_smtp_class,
    ):
        mock_settings.SMTP_HOST = "smtp.example.com"
        mock_settings.SMTP_PORT = 587
        mock_settings.SMTP_FROM = "noreply@example.com"
        mock_settings.SMTP_USER = ""
        mock_settings.SMTP_PASSWORD = ""
        mock_smtp_class.side_effect = OSError(101, "Network is unreachable")

        _send_checkin_email("guest@example.com", 1, date(2026, 5, 1), date(2026, 5, 5))


async def test_get_bookings_and_notify_error_logged():
    """Errors in individual booking processing are logged, not raised."""
    from unittest.mock import AsyncMock

    from src.tasks.tasks import _get_bookings_and_notify

    mock_booking = MagicMock(id=99, date_from="2026-05-01", date_to="2026-05-05")
    rows = [{"booking": mock_booking, "email": "a@test.com"}]

    mock_db_inner = AsyncMock()
    mock_db_inner.bookings.get_today_checkins_with_emails.return_value = rows

    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value = mock_db_inner

    with (
        patch("src.tasks.tasks.DBManager", return_value=mock_ctx),
        patch("src.tasks.tasks.send_checkin_email_task") as mock_task,
    ):
        mock_task.delay.side_effect = Exception("Celery down")
        await _get_bookings_and_notify()  # should not raise
