import logging
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path

from src.tasks.celery_app import celery_instance

logger = logging.getLogger(__name__)


@celery_instance.task(
    name="backup_database",
    autoretry_for=(Exception,),
    max_retries=2,
    default_retry_delay=300,
)
def backup_database() -> dict:
    """
    Создаёт pg_dump базы данных в сжатом формате (.sql.gz).
    Хранит бэкапы в BACKUP_DIR, удаляет файлы старше BACKUP_RETAIN_DAYS.
    """
    from src.config import settings

    backup_dir: Path = settings.BACKUP_DIR
    backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = backup_dir / f"backup_{timestamp}.sql.gz"

    env_vars = {
        "PGPASSWORD": settings.DB_PASS,
    }

    pg_dump_cmd = [
        "pg_dump",
        "-h",
        settings.DB_HOST,
        "-p",
        str(settings.DB_PORT),
        "-U",
        settings.DB_USER,
        "-d",
        settings.DB_NAME,
        "--no-password",
        "-F",
        "p",  # plain SQL format
    ]
    gzip_cmd = ["gzip", "-c"]

    logger.info("Запуск бэкапа БД → %s", filename)

    with open(filename, "wb") as out_file:
        pg_dump = subprocess.Popen(
            pg_dump_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env={**__import__("os").environ, **env_vars},
        )
        gzip = subprocess.Popen(
            gzip_cmd,
            stdin=pg_dump.stdout,
            stdout=out_file,
            stderr=subprocess.PIPE,
        )
        pg_dump.stdout.close()  # позволяет pg_dump получить SIGPIPE при выходе gzip
        _, gzip_err = gzip.communicate()
        pg_dump.wait()

    if pg_dump.returncode != 0:
        _, pg_err = pg_dump.communicate()
        filename.unlink(missing_ok=True)
        raise RuntimeError(f"pg_dump завершился с кодом {pg_dump.returncode}: {pg_err.decode()}")

    size_kb = filename.stat().st_size // 1024
    logger.info("Бэкап создан: %s (%d KB)", filename, size_kb)

    # Удаляем бэкапы старше BACKUP_RETAIN_DAYS
    cutoff = datetime.now(tz=timezone.utc) - timedelta(days=settings.BACKUP_RETAIN_DAYS)
    removed = []
    for old_file in backup_dir.glob("backup_*.sql.gz"):
        if datetime.fromtimestamp(old_file.stat().st_mtime, tz=timezone.utc) < cutoff:
            old_file.unlink()
            removed.append(old_file.name)
            logger.info("Удалён устаревший бэкап: %s", old_file.name)

    return {
        "file": str(filename),
        "size_kb": size_kb,
        "removed": removed,
    }
