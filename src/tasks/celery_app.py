from celery import Celery

from src.config import settings

celery_instance = Celery(
    "tasks",
    broker=settings.REDIS_URL,
    include=["src.tasks.tasks"],
)

celery_instance.conf.beat_schedule = {
    "send-checkin-emails-every-day": {
        "task": "booking_today_checkin",
        "schedule": 86400,  # раз в сутки (в секундах)
    }
}
