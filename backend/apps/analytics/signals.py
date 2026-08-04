# backend/apps/analytics/signals.py
"""Django signals for automatic event tracking."""

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.requests.models import Request
from apps.quotes.models import Quote
from apps.analytics.services import analytics


@receiver(post_save, sender=Request)
def track_request_created(sender, instance, created, **kwargs):
    if created:
        analytics.capture(
            instance.customer_id,
            "rfq_created",
            {
                "request_id": instance.id,
                "items_count": instance.items.count() if hasattr(instance, "items") else 0,
                "status": instance.status,
            },
        )


@receiver(post_save, sender=Quote)
def track_quote_received(sender, instance, created, **kwargs):
    if created:
        analytics.capture(
            instance.request.customer_id,
            "quote_received",
            {
                "request_id": instance.request_id,
                "supplier_id": instance.supplier_id,
                "price": str(instance.total_price) if hasattr(instance, "total_price") else None,
            },
        )
