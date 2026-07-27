"""Email service: RFQ codes, reply addresses, templates."""
import hashlib, secrets, string
from datetime import datetime, timedelta
from django.conf import settings

def generate_request_code(length=6):
    chars = string.ascii_uppercase + string.digits
    chars = chars.translate(str.maketrans('', '', '0O1IL'))
    while True:
        code = ''.join(secrets.choice(chars) for _ in range(length))
        from apps.requests.models import Request
        if not Request.objects.filter(code=code).exists():
            return code

def generate_reply_address(request_code, supplier_id):
    seed = f'{request_code}:{supplier_id}:{secrets.token_hex(4)}'
    inv_hash = hashlib.sha256(seed.encode()).hexdigest()[:6]
    return f'rfq-{request_code}-{inv_hash}@{settings.INBOUND_EMAIL_DOMAIN}'

def generate_quote_token():
    return secrets.token_urlsafe(32)

def parse_reply_address(email_addr):
    import re
    m = re.match(r'rfq-([A-Z0-9]+)-([a-z0-9]+)@', email_addr)
    return (m.group(1), m.group(2)) if m else None

RFQ_TEMPLATE_TEXT = """Здравствуйте, {supplier_name}!

По закупке RFQ-{request_code} просим предоставить коммерческое предложение.

Позиции:
{items_list}

Доставка: {delivery_address}
Срок ответа: {deadline}

Заполнить КП: {quote_url}
Или ответьте на это письмо.

Код закупки: {request_code}

С уважением, Минитендер"""

RFQ_TEMPLATE_HTML = """<html><body>
<h2>Запрос КП: RFQ-{request_code}</h2>
<p>Здравствуйте, {supplier_name}!</p>
<p>Позиции:</p><ul>{items_html}</ul>
<p>Доставка: {delivery_address}<br>Срок: {deadline}</p>
<p><a href="{quote_url}">Заполнить КП на сайте</a></p>
<p>Код закупки: {request_code}</p>
<p>С уважением, Минитендер</p>
</body></html>"""

def build_rfq_email(invitation):
    req = invitation.request
    items = req.items.filter(is_confirmed=True)
    items_list = '\n'.join(f'{i+1}. {item.name} - {item.quantity} {item.unit.short_name}'
                           for i, item in enumerate(items))
    items_html = ''.join(f'<li>{item.name} - {item.quantity} {item.unit.short_name}</li>'
                         for item in items)

    ctx = {
        'supplier_name': invitation.supplier.name,
        'request_code': req.code,
        'items_list': items_list,
        'items_html': items_html,
        'delivery_address': req.address.address if req.address else 'Ne ukazan',
        'deadline': (invitation.created_at + timedelta(days=3)).strftime('%d.%m.%Y'),
        'quote_url': f'https://app.минитендер.рф/quote/{invitation.quote_token}',
    }
    return {
        'subject': f'[RFQ-{req.code}] Запрос КП: стройматериалы',
        'body_text': RFQ_TEMPLATE_TEXT.format(**ctx),
        'body_html': RFQ_TEMPLATE_HTML.format(**ctx),
        'reply_to': invitation.reply_email,
    }

def create_rfq_invitation(request_obj, supplier):
    from apps.quotes.models import RfqInvitation
    code = generate_request_code()
    inv = RfqInvitation.objects.create(
        request=request_obj,
        supplier=supplier,
        code=code,
        reply_email=generate_reply_address(code, supplier.id),
        quote_token=generate_quote_token(),
    )
    return inv


def process_inbound_email_reply(request_code, invitation_hash, sender,
                                 subject, body_text, body_html="",
                                 message_id="", headers=None):
    """Process inbound email: attach to request, create draft quote."""
    import logging
    from django.utils import timezone
    from apps.requests.models import Request
    from apps.quotes.models import Quote, RfqInvitation, EmailMessage

    logger = logging.getLogger(__name__)

    try:
        req = Request.objects.get(code=request_code)
    except Request.DoesNotExist:
        logger.warning("Request not found: %s", request_code)
        return

    try:
        invitation = RfqInvitation.objects.select_related("supplier").get(
            request=req,
            reply_email__contains=invitation_hash,
        )
    except RfqInvitation.DoesNotExist:
        logger.warning("Invitation not found for hash: %s", invitation_hash)
        return

    EmailMessage.objects.create(
        direction="inbound",
        from_email=sender,
        to_email=invitation.reply_email,
        subject=subject,
        body_text=body_text,
        body_html=body_html,
        message_id=message_id or "",
        request=req,
        supplier=invitation.supplier,
    )

    quote, created = Quote.objects.get_or_create(
        request=req,
        supplier=invitation.supplier,
        invitation=invitation,
        defaults={"status": "received"},
    )

    invitation.status = "replied"
    invitation.replied_at = timezone.now()
    invitation.save(update_fields=["status", "replied_at"])

    logger.info(
        "Processed reply: request=%s, supplier=%s, quote=%s",
        request_code, invitation.supplier.name, quote.id,
    )
