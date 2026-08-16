"""Async email tasks."""
import logging
from django.conf import settings
from celery import shared_task

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=15)
def send_rfq_email_task(self, invitation_id):
    """Send single RFQ email with retry."""
    from django.core.mail import EmailMultiAlternatives
    from apps.quotes.models import RfqInvitation, EmailMessage
    from apps.emails.services import build_rfq_email
    from django.utils import timezone

    try:
        inv = RfqInvitation.objects.select_related("supplier", "request").get(id=invitation_id)
        email_data = build_rfq_email(inv)
        msg = EmailMultiAlternatives(
            subject=email_data["subject"],
            body=email_data["body_text"],
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[inv.supplier.email],
            reply_to=[inv.reply_email],
        )
        if email_data.get("body_html"):
            msg.attach_alternative(email_data["body_html"], "text/html")

        msg.send(fail_silently=False)

        EmailMessage.objects.create(
            direction="outbound",
            from_email="rfq@xn--d1abbjawic3ap.xn--p1ai",
            to_email=inv.supplier.email,
            subject=email_data["subject"],
            body_text=email_data["body_text"],
            request=inv.request,
            supplier=inv.supplier,
        )

        inv.status = "sent"
        inv.sent_at = timezone.now()
        inv.save(update_fields=["status", "sent_at"])
        return {"status": "ok", "invitation_id": inv.id}
    except Exception as exc:
        logger.exception("RFQ email task failed for invitation %s", invitation_id)
        raise self.retry(exc=exc)
