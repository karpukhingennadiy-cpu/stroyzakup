import os
from django.conf import settings
"""Send RFQ emails to matched suppliers."""
from django.core.mail import EmailMultiAlternatives
from apps.emails.services import create_rfq_invitation, build_rfq_email
from apps.suppliers.models import Supplier
from apps.quotes.models import EmailMessage

def send_rfq_to_suppliers(request_obj, supplier_ids):
    """Send RFQ to selected suppliers. Requires explicit supplier_ids list."""
    import logging
    from django.utils import timezone

    logger = logging.getLogger(__name__)
    suppliers = Supplier.objects.filter(id__in=supplier_ids, is_active=True)
    skipped = Supplier.objects.filter(id__in=supplier_ids, is_active=False)
    results = []

    for s in skipped:
        results.append({"supplier": s.name, "status": "skipped", "reason": "inactive"})

    for supplier in suppliers:
        if not supplier.email or "@" not in supplier.email:
            results.append({"supplier": supplier.name, "status": "skipped", "reason": "invalid email"})
            continue

        inv = create_rfq_invitation(request_obj, supplier)
        email_data = build_rfq_email(inv)
        msg = EmailMultiAlternatives(
            subject=email_data["subject"], body=email_data["body_text"],
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[supplier.email], reply_to=[inv.reply_email])
        if email_data.get("body_html"):
            msg.attach_alternative(email_data["body_html"], "text/html")
        try:
            msg.send(fail_silently=False)
            EmailMessage.objects.create(
                direction="outbound", from_email=settings.DEFAULT_FROM_EMAIL,
                to_email=supplier.email, subject=email_data["subject"],
                body_text=email_data["body_text"], request=request_obj, supplier=supplier)
            inv.status = "sent"
            inv.sent_at = timezone.now()
            results.append({"supplier": supplier.name, "status": "sent", "reply_to": inv.reply_email})
        except Exception as e:
            logger.error("RFQ send failed for %s: %s", supplier.email, e)
            results.append({"supplier": supplier.name, "status": "error", "error": str(e)})
        inv.save()

    sent_count = sum(1 for r in results if r.get("status") == "sent")
    if sent_count == 0:
        request_obj.status = "rfq_failed"
    else:
        request_obj.status = "rfq_sent"
    request_obj.save(update_fields=["status"])
    return results
