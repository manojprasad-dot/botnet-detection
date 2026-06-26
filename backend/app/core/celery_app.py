"""
KOVIRX — Celery Task Queue Setup.
"""

import logging
from celery import Celery

from app.core.config import settings

logger = logging.getLogger("kovirx.celery")

celery_app = Celery(
    "kovirx",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

# Autodiscover tasks from the app modules
celery_app.autodiscover_tasks(["app.services"])
