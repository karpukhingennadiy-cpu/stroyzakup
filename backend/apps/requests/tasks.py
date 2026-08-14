"""Async tasks for request processing."""
import logging
from celery import shared_task
from django.db import transaction

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def parse_request_task(self, request_id):
    """Parse request text via LLM asynchronously."""
    from apps.requests.models import Request
    from apps.requests.services.parser import parse_material_list

    try:
        req = Request.objects.get(id=request_id)
        req.status = "parsing"
        req.save(update_fields=["status"])

        result = parse_material_list(req)

        req.refresh_from_db()
        if "error" in result:
            # Align with the sync path (FIX-K1): 'parse_failed' is not a valid
            # status and would brick the request (views only re-parse 'draft')
            req.status = "draft"
            req.save(update_fields=["status"])
            return {"status": "failed", "error": result["error"]}

        req.status = "parsed"
        req.save(update_fields=["status"])
        return {
            "status": "ok",
            "items_count": len(result.get("items", [])),
            "clarifications": result.get("clarifications", []),
        }
    except Exception as exc:
        logger.exception("Parse task failed for request %s", request_id)
        try:
            req = Request.objects.get(id=request_id)
            req.status = "draft"  # see FIX-K1: 'parse_failed' is not a valid status
            req.save(update_fields=["status"])
        except Exception:
            pass
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def match_suppliers_task(self, request_id, limit=20):
    """Match suppliers for a request asynchronously."""
    from apps.requests.models import Request
    from apps.requests.services.matcher import match_suppliers

    try:
        req = Request.objects.get(id=request_id)
        req.status = "matching"
        req.save(update_fields=["status"])

        matches = match_suppliers(req, limit)  # FIX: limit was silently dropped

        # Auto-discovery: same as sync path — find fresh real suppliers when no 2GIS sources yet
        discovered = 0
        if not any(m.get("source") == "2gis" for m in matches):
            try:
                from .services.websearch import discover_suppliers_for_request
                discovered = discover_suppliers_for_request(req) or 0
                if discovered:
                    matches = match_suppliers(req, limit)
            except Exception:
                logger.exception("Auto-discovery failed in match task")

        req.refresh_from_db()
        req.status = "matched"
        req.match_results = {"suppliers": matches, "count": len(matches), "discovered": discovered}
        req.save(update_fields=["status", "match_results"])

        return {"status": "ok", "count": len(matches)}
    except Exception as exc:
        logger.exception("Match task failed for request %s", request_id)
        try:
            req = Request.objects.get(id=request_id)
            # 'match_failed' is not a valid status; revert to 'confirmed' so the
            # user can retry matching from the UI
            req.status = "confirmed"
            req.save(update_fields=["status"])
        except Exception:
            pass
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def send_rfq_task(self, request_id, supplier_ids):
    """Send RFQ emails asynchronously."""
    from apps.requests.models import Request
    from apps.requests.send_rfq import send_rfq_to_suppliers

    try:
        req = Request.objects.get(id=request_id)
        results = send_rfq_to_suppliers(req, supplier_ids)
        return {"status": "ok", "results": results}
    except Exception as exc:
        logger.exception("RFQ send task failed for request %s", request_id)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=2, default_retry_delay=5)
def geocode_address_task(self, address_id):
    """Geocode address asynchronously."""
    from apps.requests.models import Address
    from apps.requests.services.geocoder import geocode

    try:
        addr = Address.objects.get(id=address_id)
        result = geocode(addr.address)
        if result:
            glat, glon, gcity, _full = result
            addr.latitude = glat
            addr.longitude = glon
            addr.city = gcity or addr.city
            addr.save(update_fields=["latitude", "longitude", "city"])
        return {"status": "ok"}
    except Exception as exc:
        logger.exception("Geocode task failed for address %s", address_id)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=1, default_retry_delay=60)
def discover_suppliers_task(self, request_id):
    """Discover new suppliers via web search asynchronously."""
    from apps.requests.models import Request
    from apps.requests.services.websearch import discover_suppliers_for_request

    try:
        req = Request.objects.get(id=request_id)
        found = discover_suppliers_for_request(req)
        return {"status": "ok", "found": found or 0}
    except Exception as exc:
        logger.exception("Discover task failed for request %s", request_id)
        raise self.retry(exc=exc)
