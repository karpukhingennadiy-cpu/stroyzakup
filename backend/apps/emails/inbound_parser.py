# backend/apps/emails/inbound_parser.py
"""B1: extract commercial-proposal data from supplier reply emails via LLM.

extract_prices_to_quote(quote, email_text):
  - LLM reads the email body, maps prices to request items, updates the quote.
  - If the email is a question (not prices), drafts an answer via llm_writer
    (scenario answer_supplier_question) and sends it only when the LLM output
    is not flagged needs_review.
Returns True when any quote data was updated.
"""
import json
import logging
import re

from django.conf import settings

from apps.requests.llm_client import llm

logger = logging.getLogger(__name__)

EXTRACT_PROMPT = """Ты читаешь ответ поставщика на запрос коммерческого предложения по стройматериалам.

Позиции заявки (id, наименование, количество, единица):
{items_block}

Текст письма поставщика:
\"\"\"
{email_text}
\"\"\"

Задача: извлеки коммерческое предложение. Ответь СТРОГО валидным JSON без markdown:
{{
  "is_question": false,
  "question": "",
  "delivery_cost": null,
  "delivery_time": "",
  "payment_terms": "",
  "comment": "",
  "items": [{{"request_item_id": 1, "price": 123.45, "is_analog": false, "brand": ""}}]
}}

Правила:
- is_question=true, если письмо — это вопрос или уточнение БЕЗ цен (тогда items пустой, question — суть вопроса).
- price — цена за единицу в рублях, числом. Только явно указанные цены, ничего не выдумывай.
- request_item_id — только id из списка позиций выше. Если цену нельзя отнести к позиции — пропусти её.
- is_analog=true, если поставщик предлагает аналог/замену (brand — чем заменяет).
- delivery_cost — стоимость доставки числом или null.
- Если цен в письме нет и вопроса нет — верни items: [] и is_question: false.
"""


def _strip_html(text: str) -> str:
    text = re.sub(r"<style.*?</style>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def extract_prices_to_quote(quote, email_text: str) -> bool:
    if not llm.api_key:
        logger.info("LLM_API_KEY not set — inbound parsing skipped")
        return False
    email_text = _strip_html(email_text or "")[:6000]
    if len(email_text) < 5:
        return False

    req = quote.request
    items = req.items.filter(is_confirmed=True)
    if not items.exists():
        items = req.items.all()
    items_block = "\n".join(
        f"- id={i.id}: {i.name} — {i.quantity} {i.unit.short_name if i.unit else ''}"
        for i in items
    )
    try:
        result = llm.chat([
            {"role": "user", "content": EXTRACT_PROMPT.format(
                items_block=items_block, email_text=email_text)},
        ])
        content = result["choices"][0]["message"]["content"].strip()
        content = re.sub(r"^```(?:json)?\s*", "", content)
        content = re.sub(r"\s*```$", "", content)
        data = json.loads(content)
    except Exception:
        logger.exception("Inbound LLM extraction failed for quote %s", quote.id)
        return False

    if data.get("is_question"):
        _answer_supplier_question(quote, str(data.get("question", "")) or email_text)
        return False

    changed = False
    valid_ids = {i.id for i in items}
    from apps.quotes.models import QuoteItem
    for item_data in data.get("items", []):
        try:
            ri_id = int(item_data.get("request_item_id"))
            price = float(item_data.get("price"))
        except (TypeError, ValueError):
            continue
        if ri_id not in valid_ids or price <= 0:
            continue
        QuoteItem.objects.update_or_create(
            quote=quote, request_item_id=ri_id,
            defaults={
                "price": price,
                "is_analog": bool(item_data.get("is_analog", False)),
                "brand": str(item_data.get("brand", ""))[:200],
                "confidence": 0.8,
            },
        )
        changed = True

    update_fields = []
    if data.get("delivery_cost") is not None:
        try:
            quote.delivery_cost = float(data["delivery_cost"])
            update_fields.append("delivery_cost")
        except (TypeError, ValueError):
            pass
    for field, key in (("delivery_time", "delivery_time"),
                       ("payment_terms", "payment_terms"),
                       ("comment", "comment")):
        value = str(data.get(key, "") or "")[:500]
        if value:
            setattr(quote, field, value)
            update_fields.append(field)
    if update_fields:
        quote.save(update_fields=update_fields)
        changed = True
    return changed


def _answer_supplier_question(quote, question: str):
    """B9: draft and (when safe) send an LLM answer to the supplier's question."""
    from django.core.mail import EmailMultiAlternatives
    from apps.quotes.models import EmailMessage
    from .llm_writer import generate_email

    invitation = quote.invitation
    if not invitation:
        return
    answer = generate_email(
        "answer_supplier_question",
        request_obj=quote.request,
        supplier=quote.supplier,
        context={"supplier_question": question[:1000]},
    )
    if not answer:
        return
    EmailMessage.objects.create(
        direction="outbound",
        from_email="rfq@xn--d1abbjawic3ap.xn--p1ai",
        to_email=quote.supplier.email,
        subject=answer["subject"],
        body_text=answer["body_text"],
        request=quote.request,
        supplier=quote.supplier,
    )
    if answer.get("needs_review"):
        logger.warning(
            "Auto-answer to %s flagged needs_review: %s",
            quote.supplier.email, answer.get("review_reason"),
        )
        return
    if not quote.supplier.email:
        return
    try:
        msg = EmailMultiAlternatives(
            subject=answer["subject"], body=answer["body_text"],
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[quote.supplier.email], reply_to=[invitation.reply_email],
        )
        msg.attach_alternative(answer["body_html"], "text/html")
        msg.send(fail_silently=False)
        logger.info("Auto-answer sent to %s", quote.supplier.email)
    except Exception:
        logger.exception("Auto-answer send failed to %s", quote.supplier.email)
