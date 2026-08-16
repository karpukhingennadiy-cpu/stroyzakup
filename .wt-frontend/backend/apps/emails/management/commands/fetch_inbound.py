# backend/apps/emails/management/commands/fetch_inbound.py
"""B1: poll an IMAP mailbox for supplier replies and feed them into
process_inbound_email_reply. Run on schedule (cron / Celery beat).

Settings (via .env):
    INBOUND_IMAP_HOST, INBOUND_IMAP_PORT (993), INBOUND_IMAP_USER,
    INBOUND_IMAP_PASSWORD, INBOUND_IMAP_FOLDER (INBOX)
"""
import email
import imaplib
import logging
from email.header import decode_header

from django.conf import settings
from django.core.management.base import BaseCommand

from apps.emails.services import parse_reply_address, process_inbound_email_reply

logger = logging.getLogger(__name__)


def _decode_header_value(value: str) -> str:
    if not value:
        return ""
    parts = decode_header(value)
    out = []
    for text, charset in parts:
        if isinstance(text, bytes):
            out.append(text.decode(charset or "utf-8", errors="replace"))
        else:
            out.append(text)
    return "".join(out)


def _extract_body(msg) -> tuple[str, str]:
    """Returns (text, html) bodies."""
    text, html_body = "", ""
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            disp = str(part.get("Content-Disposition") or "")
            if "attachment" in disp:
                continue
            payload = part.get_payload(decode=True)
            if payload is None:
                continue
            charset = part.get_content_charset() or "utf-8"
            decoded = payload.decode(charset, errors="replace")
            if ctype == "text/plain" and not text:
                text = decoded
            elif ctype == "text/html" and not html_body:
                html_body = decoded
    else:
        payload = msg.get_payload(decode=True)
        if payload is not None:
            charset = msg.get_content_charset() or "utf-8"
            decoded = payload.decode(charset, errors="replace")
            if msg.get_content_type() == "text/html":
                html_body = decoded
            else:
                text = decoded
    return text, html_body


class Command(BaseCommand):
    help = "Fetch supplier replies from the inbound IMAP mailbox (B1)"

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=50)
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        host = getattr(settings, "INBOUND_IMAP_HOST", "")
        user = getattr(settings, "INBOUND_IMAP_USER", "")
        password = getattr(settings, "INBOUND_IMAP_PASSWORD", "")
        if not host or not user or not password:
            self.stderr.write(
                "INBOUND_IMAP_HOST/USER/PASSWORD not configured — nothing to fetch"
            )
            return
        port = int(getattr(settings, "INBOUND_IMAP_PORT", 993))
        folder = getattr(settings, "INBOUND_IMAP_FOLDER", "INBOX")
        limit = options["limit"]

        processed = skipped = errors = 0
        conn = imaplib.IMAP4_SSL(host, port)
        try:
            conn.login(user, password)
            conn.select(folder)
            typ, data = conn.search(None, "UNSEEN")
            if typ != "OK":
                self.stderr.write("IMAP search failed")
                return
            ids = data[0].split()[:limit]
            for msg_id in ids:
                try:
                    typ, msg_data = conn.fetch(msg_id, "(RFC822)")
                    if typ != "OK":
                        errors += 1
                        continue
                    msg = email.message_from_bytes(msg_data[0][1])
                    to_hdr = _decode_header_value(msg.get("To", ""))
                    cc_hdr = _decode_header_value(msg.get("Cc", ""))
                    sender = _decode_header_value(msg.get("From", ""))
                    subject = _decode_header_value(msg.get("Subject", ""))
                    message_id = msg.get("Message-ID", "")
                    text, html_body = _extract_body(msg)

                    reply_code = None
                    for addr_part in (to_hdr + "," + cc_hdr).split(","):
                        reply_code = parse_reply_address(addr_part.strip())
                        if reply_code:
                            break
                    if not reply_code:
                        skipped += 1
                        continue
                    if not options["dry_run"]:
                        quote = process_inbound_email_reply(
                            reply_code=reply_code, sender=sender, subject=subject,
                            body_text=text, body_html=html_body, message_id=message_id,
                        )
                        if quote is None:
                            skipped += 1
                            continue
                    processed += 1
                    # mark as seen
                    conn.store(msg_id, "+FLAGS", "\\Seen")
                except Exception:
                    logger.exception("Failed to process inbound message %s", msg_id)
                    errors += 1
        finally:
            try:
                conn.logout()
            except Exception:
                pass

        self.stdout.write(
            f"fetch_inbound: processed={processed} skipped={skipped} errors={errors}"
        )
