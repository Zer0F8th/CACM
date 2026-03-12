from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery = Celery(
    "cacm_worker",
    broker=str(settings.redis_dsn),
    backend=str(settings.redis_dsn),
)

celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    result_expires=3600,
    beat_schedule={
        "nightly-baseline-collection": {
            "task": "cacm.collect_baseline",
            "schedule": crontab(hour=2, minute=0),
            "args": ["all"],
        },
    },
)

celery.autodiscover_tasks(["app.worker"])
