# backend/apps/analytics/signals.py
"""Django signals for automatic event tracking via Celery."""

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.requests.models import Request
from apps.quotes.models import Quote
from apps.analytics.services import analytics
from apps.analytics.tasks import track_event


def _hash_user_id(user_id: int | str) -> str:
    return analytics._hash_user_id(user_id)


@receiver(post_save, sender=Request)
def track_request_created(sender, instance, created, **kwargs):
    if created:
        track_event.delay(
            event="rfq_created",
            distinct_id=_hash_user_id(instance.customer_id),
            properties={
                "request_id": instance.id,
                "items_count": instance.items.count() if hasattr(instance, "items") else 0,
                "status": instance.status,
            },
        )


@receiver(post_save, sender=Request)
def track_supplier_matched(sender, instance, created, **kwargs):
    """Отправляет supplier_matched когда заявка переходит в статус 'matched'."""
    if not created and instance.status == "matched" and instance.match_results:
        suppliers = instance.match_results.get("suppliers", [])
        track_event.delay(
            event="supplier_matched",
            distinct_id=_hash_user_id(instance.customer_id),
            properties={
                "request_id": instance.id,
                "suppliers_count": len(suppliers),
                "radius_km": _extract_radius(instance),
            },
        )


def _extract_radius(request_obj: Request) -> int | None:
    """Извлекает радиус подбора из категорий заявки."""
    try:
        categories = request_obj.items.values_list("category__default_radius_km", flat=True)
        radii = [r for r in categories if r is not None]
        return max(radii) if radii else None
    except Exception:
        return None


@receiver(post_save, sender=Quote)
def track_quote_received(sender, instance, created, **kwargs):
    if created:
        track_event.delay(
            event="quote_received",
            distinct_id=_hash_user_id(instance.request.customer_id),
            properties={
                "request_id": instance.request_id,
                "supplier_id": instance.supplier_id,
                "price": str(instance.total_price) if hasattr(instance, "total_price") else None,
            },
        )


@receiver(post_save, sender=Quote)
def track_winner_selected(sender, instance, created, **kwargs):
    """Отправляет winner_selected когда Quote переходит в статус 'selected'."""
    if not created and instance.status == "selected":
        total_price = None
        if hasattr(instance, "items"):
            try:
                from decimal import Decimal
                total_price = str(
                    sum(
                        (qi.price * qi.request_item.quantity)
                        for qi in instance.items.all()
                    )
                )
            except Exception:
                pass
        track_event.delay(
            event="winner_selected",
            distinct_id=_hash_user_id(instance.request.customer_id),
            properties={
                "request_id": instance.request_id,
                "supplier_id": instance.supplier_id,
                "total_price": total_price,
            },
        )
