from celery import Celery
from celery.schedules import crontab

from src.config import settings

celery_instance = Celery(
    "tasks",
    broker=settings.REDIS_URL,
    include=["src.tasks.tasks"],
)

celery_instance.conf.beat_schedule = {
    "send-checkin-emails-every-day": {
        "task": "booking_today_checkin",
        "schedule": crontab(hour=8, minute=0),  # ежедневно в 08:00 UTC
    }
}
