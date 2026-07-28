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

def generate_reply_address(reply_code):
    return f'rfq-{reply_code}@{settings.INBOUND_EMAIL_DOMAIN}'

def generate_quote_token():
    return secrets.token_urlsafe(32)

def parse_reply_address(email_addr):
    import re
    m = re.match(r'rfq-([A-Za-z0-9_-]+)@', email_addr)
    return m.group(1) if m else None

RFQ_TEMPLATE_TEXT = """Здравствуйте, {supplier_name}!

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
platforma dlya stroitelnykh zakupok"""

RFQ_TEMPLATE_HTML = """<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: Arial, sans-serif; max-width: 650px; margin: 0 auto; padding: 20px; color: #333;">
  <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
    <h2 style="margin: 0 0 10px; color: #1a73e8;">Запрос КП № RFQ-{request_code}</h2>
    <p style="margin: 0;">Здравствуйте, <strong>{supplier_name}</strong>!</p>
  </div>

  <p>Приглашаем вас принять участие в закупке. Просим предоставить коммерческое предложение на следующие позиции:</p>

  <table style="width: 100%; border-collapse: collapse; margin: 15px 0;">
    <tr style="background: #e8eaed;">
      <th style="padding: 10px; text-align: left; border: 1px solid #ddd;">№</th>
      <th style="padding: 10px; text-align: left; border: 1px solid #ddd;">Наименование</th>
    </tr>
    {items_html}
  </table>

  <div style="background: #fff3cd; padding: 15px; border-radius: 6px; margin: 15px 0;">
    <strong>Условия:</strong><br>
    Адрес доставки: {delivery_address}<br>
    Срок подачи КП: до <strong>{deadline}</strong>
  </div>

  <div style="text-align: center; margin: 25px 0;">
    <a href="{quote_url}" style="display: inline-block; padding: 14px 32px; background: #1a73e8; color: #fff; text-decoration: none; border-radius: 6px; font-size: 16px; font-weight: bold;">
      Заполнить КП на сайте
    </a>
    <p style="color: #666; font-size: 13px; margin-top: 8px;">Или просто ответьте на это письмо</p>
  </div>

  <hr style="border: none; border-top: 1px solid #ddd; margin: 25px 0;">
  <p style="color: #888; font-size: 13px;">
    По вопросам: ответьте на это письмо или напишите на <a href="mailto:rfq@minitender.ru">rfq@minitender.ru</a><br>
    Код закупки: RFQ-{request_code}
  </p>
  <p style="color: #999; font-size: 12px;">
    platforma dlya stroitelnykh zakupok &mdash; Минитендер.рф
  </p>
</body>
</html>"""

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
        'quote_url': f'{getattr(settings, "FRONTEND_URL", "https://app.минитендер.рф")}/quote/{invitation.quote_token}',
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
    reply_code = secrets.token_hex(8)
    inv = RfqInvitation.objects.create(
        request=request_obj,
        supplier=supplier,
        code=code,
        reply_code=reply_code,
        reply_email=generate_reply_address(reply_code),
        quote_token=generate_quote_token(),
    )
    return inv


def process_inbound_email_reply(reply_code, sender,
                                 subject, body_text, body_html="",
                                 message_id="", headers=None):
    """Process inbound email: find invitation by reply_code, create draft quote."""
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