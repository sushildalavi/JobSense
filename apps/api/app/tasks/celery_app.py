"""
Celery application configuration.
"""
from __future__ import annotations

from celery import Celery

from app.core.config import settings

# ── Celery app ─────────────────────────────────────────────────────────────────
celery_app = Celery(
    "applyflow",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.ingestion",
        "app.tasks.matching",
        "app.tasks.ai_tasks",
        "app.tasks.email_tasks",
        "app.tasks.calendar_tasks",
    ],
)

celery_app.conf.update(
    # Serialization
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    # Timezones
    timezone="UTC",
    enable_utc=True,
    # Result backend
    result_expires=86400,  # 24h
    # Worker settings
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    # Queue routing
    task_routes={
        "app.tasks.ingestion.*": {"queue": "ingestion"},
        "app.tasks.matching.*": {"queue": "matching"},
        "app.tasks.ai_tasks.*": {"queue": "ai"},
        "app.tasks.email_tasks.*": {"queue": "email"},
        "app.tasks.calendar_tasks.*": {"queue": "calendar"},
    },
    task_queues={
        "ingestion": {},
        "matching": {},
        "ai": {},
        "email": {},
        "calendar": {},
        "celery": {},
    },
    # Retry settings
    task_max_retries=3,
    task_default_retry_delay=60,
)
