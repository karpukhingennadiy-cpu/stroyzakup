# backend/apps/emails/services.py
'''Email service: RFQ codes, reply addresses, templates.'''
import secrets
import string
from datetime import timedelta
from django.conf import settings


# FIX-H5: переименовано, чтобы не путать с кодом заявки
def generate_invitation_code(length=8):
    chars = string.ascii_uppercase + string.digits
    chars = chars.translate(str.maketrans("", "", "0O1IL"))
    while True:
        code = "".join(secrets.choice(chars) for _ in range(length))
        from apps.quotes.models import RfqInvitation
        if not RfqInvitation.objects.filter(code=code).exists():
            return code


def generate_reply_address(reply_code):
    return f"rfq-{reply_code}@{settings.INBOUND_EMAIL_DOMAIN}"


def generate_quote_token():
    return secrets.token_urlsafe(32)


def parse_reply_address(email_addr):
    import re
    m = re.match(r"rfq-([A-Za-z0-9_-]+)@", email_addr)
    return m.group(1) if m else None


RFQ_TEMPLATE_TEXT = '''Здравствуйте, {supplier_name}!

Приглашаем вас принять участие в закупке № RFQ-{request_code}.
Просим предоставить коммерческое предложение на следующие позиции:

{items_list}

Условия:
- Адрес доставки: {delivery_address}
- Срок подачи КП: до {deadline}

Для заполнения КП перейдите по ссылке:
{quote_url}

Или просто ответьте на это письмо — мы получим ваше предложение.

По вопросам: ответьте на это письмо или напишите на rfq@минитендер.рф

--
С уважением,
команда Минитендер.рф
'''

# FIX-H4: полноценный HTML-шаблон с правильной таблицей
RFQ_TEMPLATE_HTML = '''<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<style>
body{{font-family:Arial,sans-serif;background:#f4f4f5;color:#18181b;line-height:1.5;}}
.container{{max-width:640px;margin:0 auto;padding:24px;background:#fff;border-radius:8px;}}
h2{{color:#ea580c;margin-top:0;}}
table{{width:100%;border-collapse:collapse;margin:16px 0;}}
th,td{{padding:10px 12px;text-align:left;border-bottom:1px solid #e4e4e7;}}
th{{background:#fafafa;font-weight:600;font-size:12px;text-transform:uppercase;color:#71717a;}}
.btn{{display:inline-block;padding:12px 24px;background:#ea580c;color:#fff;text-decoration:none;border-radius:6px;font-weight:600;}}
.footer{{margin-top:24px;padding-top:16px;border-top:1px solid #e4e4e7;font-size:12px;color:#71717a;}}
</style>
</head>
<body>
<div class="container">
<h2>Запрос КП № RFQ-{request_code}</h2>
<p>Здравствуйте, <strong>{supplier_name}</strong>!</p>
<p>Приглашаем вас принять участие в закупке. Просим предоставить коммерческое предложение на следующие позиции:</p>
<table>
<thead><tr><th>№</th><th>Наименование</th><th>Кол-во</th></tr></thead>
<tbody>{items_html}</tbody>
</table>
<p><strong>Условия:</strong></p>
<ul>
<li>Адрес доставки: {delivery_address}</li>
<li>Срок подачи КП: до <strong>{deadline}</strong></li>
</ul>
<p style="text-align:center;margin:24px 0;">
<a href="{quote_url}" class="btn">Заполнить КП онлайн</a>
</p>
<p>Или просто ответьте на это письмо — мы получим ваше предложение.</p>
<div class="footer">
<p>По вопросам: ответьте на это письмо или напишите на rfq@минитендер.рф</p>
<p>© Минитендер.рф — платформа строительных закупок</p>
</div>
</div>
</body>
</html>'''


def build_rfq_email(invitation):
    req = invitation.request
    items = req.items.filter(is_confirmed=True)
    if not items.exists():
        # Fallback: include unconfirmed items rather than sending an empty list
        items = req.items.all()

    # B9: try LLM-generated invitation first; static template is the fallback
    try:
        from .llm_writer import generate_email
        llm_email = generate_email(
            "rfq_invitation",
            request_obj=req,
            supplier=invitation.supplier,
            context={
                "quote_url": f"{settings.FRONTEND_URL}/quote/{invitation.quote_token}",
                "deadline": (invitation.created_at + timedelta(days=3)).strftime("%d.%m.%Y"),
            },
        )
        if llm_email:
            return {
                "subject": llm_email["subject"],
                "body_text": llm_email["body_text"],
                "body_html": llm_email["body_html"],
                "reply_to": invitation.reply_email,
                "needs_review": llm_email["needs_review"],
                "review_reason": llm_email.get("review_reason", ""),
                "source": "llm",
            }
    except Exception:
        import logging
        logging.getLogger(__name__).exception("LLM RFQ generation failed, using template")

    import html as _html
    items_list = "\n".join(
        f"{i+1}. {item.name} — {item.quantity} {item.unit.short_name}"
        for i, item in enumerate(items)
    )
    # FIX-H4: правильная HTML-таблица с <tr><td>; SEC: escape user-supplied names
    items_html = "".join(
        f"<tr><td>{i+1}</td><td>{_html.escape(item.name)}</td>"
        f"<td>{item.quantity} {_html.escape(item.unit.short_name)}</td></tr>"
        for i, item in enumerate(items)
    )

    ctx = {
        "supplier_name": invitation.supplier.name,
        "request_code": req.code,
        "items_list": items_list,
        "items_html": items_html,
        "delivery_address": _html.escape(req.address.address if req.address else "Не указан"),
        "deadline": (invitation.created_at + timedelta(days=3)).strftime("%d.%m.%Y"),
        "quote_url": f"{settings.FRONTEND_URL}/quote/{invitation.quote_token}",
    }
    return {
        "subject": f"[RFQ-{req.code}] Запрос КП: стройматериалы",
        # text part: raw values; HTML part: user data escaped above
        "body_text": RFQ_TEMPLATE_TEXT.format(
            **{**ctx, "delivery_address": req.address.address if req.address else "Не указан"}
        ),
        "body_html": RFQ_TEMPLATE_HTML.format(**{**ctx, "supplier_name": _html.escape(ctx["supplier_name"])}),
        "reply_to": invitation.reply_email,
        "needs_review": False,
        "source": "template",
    }


def create_rfq_invitation(request_obj, supplier):
    from apps.quotes.models import RfqInvitation
    reply_code = secrets.token_hex(8)
    inv = RfqInvitation.objects.create(
        request=request_obj,
        supplier=supplier,
        code=generate_invitation_code(),  # FIX-H5
        reply_code=reply_code,
        reply_email=generate_reply_address(reply_code),
        quote_token=generate_quote_token(),
    )
    return inv


# === B7: customer notifications ===

CUSTOMER_QUOTE_TEMPLATE = """Здравствуйте!

Поставщик {supplier_name} прислал коммерческое предложение по вашей заявке RFQ-{request_code}{total_line}.

Посмотреть конкурентный лист:
{sheet_url}

--
команда Минитендер.рф
"""

CUSTOMER_SHEET_READY_TEMPLATE = """Здравствуйте!

По вашей заявке RFQ-{request_code} собраны все ответы: получено {replied} КП из {total} отправленных приглашений.

Конкурентный лист готов:
{sheet_url}

--
команда Минитендер.рф
"""


def _quote_total(quote):
    from decimal import Decimal
    total = Decimal("0")
    for qi in quote.items.select_related("request_item").all():
        total += qi.price * qi.request_item.quantity
    return total + (quote.delivery_cost or Decimal("0"))


def _send_customer_email(customer, subject, body_text, request_obj=None, supplier=None):
    import logging
    from django.core.mail import EmailMultiAlternatives
    logger = logging.getLogger(__name__)
    if not customer or not customer.email:
        return False
    try:
        msg = EmailMultiAlternatives(
            subject=subject, body=body_text,
            from_email=settings.DEFAULT_FROM_EMAIL, to=[customer.email],
        )
        msg.send(fail_silently=False)
        from apps.quotes.models import EmailMessage
        EmailMessage.objects.create(
            direction="outbound",
            from_email="rfq@xn--d1abbjawic3ap.xn--p1ai",
            to_email=customer.email, subject=subject, body_text=body_text,
            request=request_obj, supplier=supplier,
        )
        return True
    except Exception:
        logger.exception("Customer notification failed: %s", subject)
        return False


def notify_customer_quote_received(quote):
    """B7: email the customer when a supplier's quote arrives."""
    req = quote.request
    customer = req.customer
    total = _quote_total(quote)
    total_line = f" на сумму {total:,.2f} ₽".replace(",", " ") if total else ""
    sheet_url = f"{settings.FRONTEND_URL}/lk/requests/{req.id}/competitive"
    subject = f"[RFQ-{req.code}] Поставщик {quote.supplier.name} прислал КП{total_line}"
    body = CUSTOMER_QUOTE_TEMPLATE.format(
        supplier_name=quote.supplier.name, request_code=req.code,
        total_line=total_line, sheet_url=sheet_url,
    )
    sent = _send_customer_email(customer, subject, body, request_obj=req, supplier=quote.supplier)
    _maybe_notify_sheet_ready(req)
    return sent


def _maybe_notify_sheet_ready(request_obj):
    """B7: when every sent invitation has a reply, notify the customer once."""
    from apps.quotes.models import RfqInvitation, EmailMessage
    invitations = RfqInvitation.objects.filter(request=request_obj, status__in=["sent", "replied"])
    total = invitations.count()
    if total < 2:  # competitive sheet is meaningful from 2+ invitations
        return False
    replied = invitations.filter(status="replied").count()
    if replied < total:
        return False
    marker = "Конкурентный лист готов"
    already = EmailMessage.objects.filter(
        request=request_obj, direction="outbound", subject__contains=marker,
    ).exists()
    if already:
        return False
    sheet_url = f"{settings.FRONTEND_URL}/lk/requests/{request_obj.id}/competitive"
    subject = f"[RFQ-{request_obj.code}] {marker}: {replied} из {total} ответов"
    body = CUSTOMER_SHEET_READY_TEMPLATE.format(
        request_code=request_obj.code, replied=replied, total=total, sheet_url=sheet_url,
    )
    return _send_customer_email(request_obj.customer, subject, body, request_obj=request_obj)


def process_inbound_email_reply(
    reply_code, sender, subject, body_text, body_html="",
    message_id="", headers=None
):
    import logging
    from django.utils import timezone
    from apps.quotes.models import Quote, RfqInvitation, EmailMessage

    logger = logging.getLogger(__name__)

    try:
        invitation = RfqInvitation.objects.select_related("supplier", "request").get(
            reply_code=reply_code,
        )
    except RfqInvitation.DoesNotExist:
        logger.warning("Invitation not found for reply_code: %s", reply_code)
        return None

    req = invitation.request

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
        req.code, invitation.supplier.name, quote.id,
    )
    # B1: try to extract prices from the email body via LLM
    try:
        from apps.emails.inbound_parser import extract_prices_to_quote
        extract_prices_to_quote(quote, body_text or body_html)
    except Exception:
        logger.exception("Inbound price extraction failed for quote %s", quote.id)
    # B7: notify the customer about the received quote
    try:
        notify_customer_quote_received(quote)
    except Exception:
        logger.exception("Customer notification failed for quote %s", quote.id)
    return quote