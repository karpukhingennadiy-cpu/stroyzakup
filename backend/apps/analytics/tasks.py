# backend/apps/analytics/tasks.py
"""Celery tasks for async PostHog analytics tracking."""

import logging
from celery import shared_task

from apps.analytics.services import analytics

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=5)
def track_event(self, event: str, distinct_id: str, properties: dict | None = None):
    """Асинхронная отправка события в PostHog.

    Не блокирует основной поток запроса.
    При ошибке — retry с экспоненциальным backoff.
    """
    try:
        analytics.capture_raw(distinct_id, event, properties or {})
    except Exception as exc:
        logger.warning("PostHog track_event failed: %s", exc)
        raise self.retry(exc=exc)
