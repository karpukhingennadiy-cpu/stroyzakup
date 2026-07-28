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

По вопросам: ответьте на это письмо или напишите на rfq@minitender.ru

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
body{font-family:Arial,sans-serif;background:#f4f4f5;color:#18181b;line-height:1.5;}
.container{max-width:640px;margin:0 auto;padding:24px;background:#fff;border-radius:8px;}
h2{color:#ea580c;margin-top:0;}
table{width:100%;border-collapse:collapse;margin:16px 0;}
th,td{padding:10px 12px;text-align:left;border-bottom:1px solid #e4e4e7;}
th{background:#fafafa;font-weight:600;font-size:12px;text-transform:uppercase;color:#71717a;}
.btn{display:inline-block;padding:12px 24px;background:#ea580c;color:#fff;text-decoration:none;border-radius:6px;font-weight:600;}
.footer{margin-top:24px;padding-top:16px;border-top:1px solid #e4e4e7;font-size:12px;color:#71717a;}
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
<p>По вопросам: ответьте на это письмо или напишите на rfq@minitender.ru</p>
<p>© Минитендер.рф — платформа строительных закупок</p>
</div>
</div>
</body>
</html>'''


def build_rfq_email(invitation):
    req = invitation.request
    items = req.items.filter(is_confirmed=True)

    items_list = "\n".join(
        f"{i+1}. {item.name} — {item.quantity} {item.unit.short_name}"
        for i, item in enumerate(items)
    )
    # FIX-H4: правильная HTML-таблица с <tr><td>
    items_html = "".join(
        f"<tr><td>{i+1}</td><td>{item.name}</td><td>{item.quantity} {item.unit.short_name}</td></tr>"
        for i, item in enumerate(items)
    )

    ctx = {
        "supplier_name": invitation.supplier.name,
        "request_code": req.code,
        "items_list": items_list,
        "items_html": items_html,
        "delivery_address": req.address.address if req.address else "Не указан",
        "deadline": (invitation.created_at + timedelta(days=3)).strftime("%d.%m.%Y"),
        "quote_url": f"https://app.минитендер.рф/quote/{invitation.quote_token}",
    }
    return {
        "subject": f"[RFQ-{req.code}] Запрос КП: стройматериалы",
        "body_text": RFQ_TEMPLATE_TEXT.format(**ctx),
        "body_html": RFQ_TEMPLATE_HTML.format(**ctx),
        "reply_to": invitation.reply_email,
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
    return quote