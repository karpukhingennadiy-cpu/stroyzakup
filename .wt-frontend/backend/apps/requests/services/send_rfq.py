"""Send RFQ emails to selected suppliers (canonical implementation)."""
import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils import timezone

from apps.emails.services import create_rfq_invitation, build_rfq_email
from apps.suppliers.models import Supplier
from apps.quotes.models import EmailMessage

logger = logging.getLogger(__name__)

OUTBOUND_FROM = "rfq@xn--d1abbjawic3ap.xn--p1ai"  # rfq@минитендер.рф (punycode)


def send_rfq_to_suppliers(request_obj, supplier_ids):
    """Send RFQ to selected suppliers. Requires explicit supplier_ids list."""
    suppliers = Supplier.objects.filter(id__in=supplier_ids, is_active=True)
    skipped = Supplier.objects.filter(id__in=supplier_ids, is_active=False)
    results = []

    for s in skipped:
        results.append({"supplier": s.name, "status": "skipped", "reason": "inactive"})

    for supplier in suppliers:
        # Validate email before sending
        if not supplier.email or "@" not in supplier.email:
            results.append({"supplier": supplier.name, "status": "skipped", "reason": "invalid email"})
            continue

        inv = create_rfq_invitation(request_obj, supplier)
        email_data = build_rfq_email(inv)
        # B9: LLM-flagged emails are NOT sent — they wait for human review (admin)
        if email_data.get("needs_review"):
            inv.status = "pending"
            inv.save(update_fields=["status"])
            logger.warning(
                "RFQ for %s flagged needs_review: %s",
                supplier.email, email_data.get("review_reason", ""),
            )
            results.append({
                "supplier": supplier.name, "status": "needs_review",
                "reason": email_data.get("review_reason", "требует проверки человеком"),
            })
            continue
        msg = EmailMultiAlternatives(
            subject=email_data["subject"], body=email_data["body_text"],
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[supplier.email], reply_to=[inv.reply_email])
        if email_data.get("body_html"):
            msg.attach_alternative(email_data["body_html"], "text/html")
        try:
            msg.send(fail_silently=False)
            EmailMessage.objects.create(
                direction="outbound", from_email=OUTBOUND_FROM,
                to_email=supplier.email, subject=email_data["subject"],
                body_text=email_data["body_text"], request=request_obj, supplier=supplier)
            inv.status = "sent"
            inv.sent_at = timezone.now()
            results.append({"supplier": supplier.name, "status": "sent", "reply_to": inv.reply_email})
        except Exception as e:
            logger.error("RFQ send failed for %s: %s", supplier.email, e)
            results.append({"supplier": supplier.name, "status": "error", "error": str(e)})
        inv.save()

    # Final status: rfq_sent only if at least one email actually went out
    sent_count = sum(1 for r in results if r.get("status") == "sent")
    request_obj.status = "rfq_sent" if sent_count > 0 else "rfq_failed"
    request_obj.save(update_fields=["status"])
    return results
