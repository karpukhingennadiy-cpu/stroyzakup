# backend/apps/analytics/services.py
"""PostHog analytics tracking service."""

import hashlib
import os
from typing import Any

from posthog import Posthog


class AnalyticsService:
    def __init__(self):
        api_key = os.getenv("POSTHOG_API_KEY")
        host = os.getenv("POSTHOG_HOST", "https://app.posthog.com")
        self.enabled = bool(api_key)
        if self.enabled:
            self.client = Posthog(api_key, host=host)
        else:
            self.client = None

    def _hash_user_id(self, user_id: int | str) -> str:
        """Анонимизация user_id для 152-ФЗ / GDPR."""
        return hashlib.sha256(str(user_id).encode()).hexdigest()[:32]

    def capture(self, user_id: int | str, event: str, properties: dict[str, Any] | None = None):
        if not self.enabled or not self.client:
            return
        distinct_id = self._hash_user_id(user_id)
        props = properties or {}
        props["$lib"] = "minitender-backend"
        self.client.capture(distinct_id, event, props)

    def identify(self, user_id: int | str, properties: dict[str, Any] | None = None):
        if not self.enabled or not self.client:
            return
        distinct_id = self._hash_user_id(user_id)
        props = properties or {}
        # НЕ передаём PII: email, имя, телефон
        safe_props = {k: v for k, v in props.items() if k not in ("email", "name", "phone")}
        self.client.identify(distinct_id, safe_props)


# Singleton
analytics = AnalyticsService()
