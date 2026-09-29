import os
from celery import Celery
from celery.schedules import crontab

from app.core.config import get_settings

settings = get_settings()

redis_broker_url = os.getenv("REDIS_URL", settings.redis_url or "redis://localhost:6379/0")

celery_app = Celery(
    "mailsentinel_workers",
    broker=redis_broker_url,
    backend=redis_broker_url,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes maximum per task
    task_soft_time_limit=240,
    broker_connection_retry_on_startup=True,
    beat_schedule={
        # Periodic sync every 5 minutes across all connected user accounts
        "periodic-sync-all-users-inbox": {
            "task": "app.workers.tasks.sync_all_active_users_task",
            "schedule": crontab(minute="*/5"),
        },
    },
)
