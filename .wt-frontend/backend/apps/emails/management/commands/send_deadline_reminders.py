# backend/apps/emails/management/commands/send_deadline_reminders.py
"""B10: remind suppliers who haven't replied before the RFQ deadline.

Deadline = invitation.sent_at + 3 days (same as in the RFQ email).
- ~24h before deadline: reminder_24h (once)
- ~2h before deadline: reminder_2h (once)

Idempotent: reminder_*_sent_at flags prevent duplicates.
Run on schedule: cron / Celery beat, e.g. every 15 minutes.
"""
import logging
from datetime import timedelta

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.quotes.models import EmailMessage, RfqInvitation

logger = logging.getLogger(__name__)

DEADLINE_DAYS = 3
WINDOW_MINUTES = 20  # run at least every WINDOW_MINUTES for timely reminders

REMINDER_FALLBACK_TEXT = """Здравствуйте, {supplier_name}!

Напоминаем: срок подачи коммерческого предложения по закупке № RFQ-{request_code} истекает {deadline}.

Заполнить КП онлайн: {quote_url}
Или просто ответьте на это письмо.

--
С уважением,
команда Минитендер.рф
"""


def _build_reminder(invitation, scenario):
    from apps.emails.llm_writer import generate_email
    quote_url = f"{settings.FRONTEND_URL}/quote/{invitation.quote_token}"
    try:
        result = generate_email(
            scenario,
            request_obj=invitation.request,
            supplier=invitation.supplier,
            context={"quote_url": quote_url},
        )
        if result and not result.get("needs_review"):
            return result["subject"], result["body_text"], result["body_html"]
        if result and result.get("needs_review"):
            logger.warning(
                "Reminder for invitation %s flagged needs_review: %s",
                invitation.id, result.get("review_reason"),
            )
            return None
    except Exception:
        logger.exception("LLM reminder generation failed")
    req = invitation.request
    deadline = (invitation.sent_at + timedelta(days=DEADLINE_DAYS)).strftime("%d.%m.%Y %H:%M")
    subject = f"[RFQ-{req.code}] Напоминание: срок подачи КП истекает {deadline}"
    body = REMINDER_FALLBACK_TEXT.format(
        supplier_name=invitation.supplier.name, request_code=req.code,
        deadline=deadline, quote_url=quote_url,
    )
    return subject, body, None


class Command(BaseCommand):
    help = "Send deadline reminders to suppliers who haven't replied (B10)"

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        now = timezone.now()
        window = timedelta(minutes=WINDOW_MINUTES)
        pending = RfqInvitation.objects.filter(
            status="sent", sent_at__isnull=False,
        ).select_related("request", "supplier")

        sent_count = skipped = errors = 0
        for inv in pending:
            deadline = inv.sent_at + timedelta(days=DEADLINE_DAYS)
            delta = deadline - now
            scenario = flag = None
            if inv.reminder_24h_sent_at is None and timedelta(hours=2) < delta <= timedelta(hours=24):
                scenario, flag = "reminder_24h", "reminder_24h_sent_at"
            elif inv.reminder_2h_sent_at is None and timedelta(0) < delta <= timedelta(hours=2):
                scenario, flag = "reminder_2h", "reminder_2h_sent_at"
            if not scenario:
                skipped += 1
                continue
            if not inv.supplier.email:
                skipped += 1
                continue

            built = _build_reminder(inv, scenario)
            if built is None:
                errors += 1  # needs human review — not sent, retry next run
                continue
            subject, body_text, body_html = built
            if options["dry_run"]:
                self.stdout.write(f"[dry-run] {scenario} -> {inv.supplier.email}: {subject}")
                sent_count += 1
                continue
            try:
                msg = EmailMultiAlternatives(
                    subject=subject, body=body_text,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[inv.supplier.email], reply_to=[inv.reply_email],
                )
                if body_html:
                    msg.attach_alternative(body_html, "text/html")
                msg.send(fail_silently=False)
                EmailMessage.objects.create(
                    direction="outbound",
                    from_email="rfq@xn--d1abbjawic3ap.xn--p1ai",
                    to_email=inv.supplier.email, subject=subject,
                    body_text=body_text, request=inv.request, supplier=inv.supplier,
                )
                setattr(inv, flag, now)
                inv.save(update_fields=[flag])
                sent_count += 1
            except Exception:
                logger.exception("Reminder send failed for invitation %s", inv.id)
                errors += 1

        self.stdout.write(
            f"send_deadline_reminders: sent={sent_count} skipped={skipped} errors={errors}"
        )
