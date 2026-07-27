
"""Email views: webhook for inbound email processing."""
import hashlib
import hmac
import json
import logging

from django.conf import settings
from django.http import HttpResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .services import parse_reply_address

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def mailgun_inbound_webhook(request):
    """Receive inbound emails from Mailgun/transactional provider webhook."""
    token = request.POST.get("token", "")
    timestamp = request.POST.get("timestamp", "")
    signature = request.POST.get("signature", "")
    secret = getattr(settings, "INBOUND_EMAIL_WEBHOOK_SECRET", "")

    if secret:
        h = hmac.new(secret.encode(), f"{timestamp}{token}".encode(), hashlib.sha256)
        computed = h.hexdigest()
        if not hmac.compare_digest(computed, signature):
            logger.warning("Invalid webhook signature")
            return HttpResponseForbidden("Invalid signature")

    recipient = request.POST.get("recipient", "")
    sender = request.POST.get("sender", "")
    subject = request.POST.get("subject", "")
    body_text = request.POST.get("stripped-text", "")
    body_html = request.POST.get("body-html", "")
    message_id = request.POST.get("message-id", "")

    parsed = parse_reply_address(recipient)
    if parsed:
        reply_code = parsed
        from apps.emails.services import process_inbound_email_reply
        process_inbound_email_reply(
            reply_code=reply_code,
            sender=sender,
            subject=subject,
            body_text=body_text,
            body_html=body_html,
            message_id=message_id,
        )
    return HttpResponse("OK")


@csrf_exempt
@require_POST
def generic_inbound_webhook(request):
    """Generic inbound webhook for SendGrid or other providers."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponse("Invalid JSON", status=400)

    envelopes = data.get("envelope", data) if isinstance(data, dict) else {}
    recipients = envelopes.get("to", [])
    sender = envelopes.get("from", "")
    subject = data.get("subject", "")
    body_text = data.get("text", data.get("stripped-text", ""))
    body_html = data.get("html", data.get("body-html", ""))

    recipient = recipients[0] if recipients else ""
    parsed = parse_reply_address(recipient)
    if parsed:
        reply_code = parsed
        from apps.emails.services import process_inbound_email_reply
        process_inbound_email_reply(
            reply_code=reply_code,
            sender=sender,
            subject=subject,
            body_text=body_text,
            body_html=body_html,
        )
    return HttpResponse("OK")
