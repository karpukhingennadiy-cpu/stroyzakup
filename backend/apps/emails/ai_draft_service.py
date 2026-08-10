# backend/apps/emails/ai_draft_service.py
# High-level draft service (B9): build context -> call LLM -> parse Pydantic
# -> sanitize HTML -> post-validate. Caches 1h, logs to AiEmailLog, falls
# back to static RFQ templates with needs_review=True when the LLM fails.

import json
import logging

from django.core.cache import cache

from .html_sanitizer import sanitize_html
from .prompt_builder import build_request_context, build_scenario_data
from .schemas import EmailDraftResponse

logger = logging.getLogger(__name__)

CACHE_TTL = 60 * 60  # 1h
NL = chr(10)
Q = chr(34)


def generate_draft(scenario, request_obj, supplier=None, context=None, timeout=60):
    """Generate a validated EmailDraftResponse.

    Returns (response, source) where source is 'llm' or 'template'.
    The template fallback always flags needs_review=True (human check).
    """
    from .llm_writer import generate_email

    key = _cache_key(scenario, request_obj, supplier, context)
    cached = cache.get(key)
    if cached is not None:
        return EmailDraftResponse(**cached), "cache"

    result = generate_email(scenario, request_obj, supplier, context, timeout=timeout)
    if result is not None:
        out = EmailDraftResponse(
            subject=result["subject"],
            body_text=result["body_text"],
            body_html=result["body_html"],
            needs_review=result["needs_review"],
            safety_reason=result.get("review_reason") or "",
        )
        cache.set(key, _to_dict(out), CACHE_TTL)
        return out, "llm"

    # Static fallback: reuse the RFQ template for invitations; generic draft
    # for every other scenario. needs_review=True -> queue for human check.
    static = _static_fallback(scenario, request_obj, supplier, context or {})
    return static, "template"


def _to_dict(response: EmailDraftResponse) -> dict:
    return {
        "subject": response.subject,
        "body_text": response.body_text,
        "body_html": response.body_html,
        "needs_review": response.needs_review,
        "safety_reason": response.safety_reason,
    }


def _cache_key(scenario, request_obj, supplier, context) -> str:
    import hashlib
    raw = json.dumps(
        {
            "scenario": scenario,
            "req": [request_obj.id, str(request_obj.updated_at)] if request_obj else None,
            "sup": [supplier.id] if supplier else None,
            "ctx": context or {},
        },
        sort_keys=True,
        ensure_ascii=False,
        default=str,
    )
    return "email_draft:" + hashlib.sha256(raw.encode()).hexdigest()


def _static_fallback(scenario, request_obj, supplier, context) -> EmailDraftResponse:
    from django.conf import settings

    supplier_name = supplier.name if supplier else "поставщик"
    code = request_obj.code if request_obj else ""
    quote_url = context.get("quote_url") or (f"{settings.FRONTEND_URL}/quote/" if hasattr(settings, "FRONTEND_URL") else "")
    deadline = context.get("deadline") or ""

    if scenario == "rfq_invitation":
        body = (
            f"Здравствуйте, {supplier_name}!" + NL + NL +
            f"Приглашаем вас принять участие в закупке № RFQ-{code}." + NL +
            f"Просим предоставить коммерческое предложение на позиции заявки." + NL +
            f"Адрес доставки: {_addr(request_obj)}" + NL +
            f"Срок подачи КП: до {deadline}" + NL + NL +
            f"Ссылка для заполнения КП: {quote_url}" + NL + NL +
            "--" + NL + "команда Минитендер.рф"
        )
        subject = f"[RFQ-{code}] Запрос КП: стройматериалы"
    else:
        body = (
            f"Здравствуйте, {supplier_name}!" + NL + NL +
            f"По закупке № RFQ-{code}:" + NL + _addr(request_obj) + NL + NL +
            "--" + NL + "команда Минитендер.рф"
        )
        subject = f"[RFQ-{code}] Уведомление"

    return EmailDraftResponse(
        subject=subject,
        body_text=body,
        body_html=sanitize_html(_simple_html(subject, body)),
        needs_review=True,
        safety_reason="AI недоступен, проверьте вручную",
    )


def _addr(request_obj) -> str:
    if request_obj and request_obj.address:
        return request_obj.address.address or "не указан"
    return "не указан"


def _simple_html(subject: str, body_text: str) -> str:
    import html
    escaped = html.escape(body_text)
    paragraphs = [p.replace(chr(10), "<br>") for p in escaped.split(chr(10) * 2)]
    inner = "".join(f"<p>{p}</p>" for p in paragraphs if p.strip())
    head = "<!DOCTYPE html><html lang=" + Q + "ru" + Q + "><head><meta charset=" + Q + "UTF-8" + Q + "></head>"
    style = "<body style=" + Q + "font-family:Arial,sans-serif;line-height:1.5;color:#18181b;" + Q + ">"
    div = "<div style=" + Q + "max-width:640px;margin:0 auto;padding:24px;" + Q + ">"
    return head + style + div + inner + "</div></body></html>"
