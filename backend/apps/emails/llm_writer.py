# backend/apps/emails/llm_writer.py
"""LLM email writer (B9).

generate_email(scenario, request_obj, supplier, context) ->
    {"subject", "body_text", "body_html", "needs_review", "review_reason", "source"}

- JSON-validated LLM output, cached by context hash.
- Post-generation safety scan: forbidden phrases or missing request code
  force needs_review=True.
- Returns None when LLM is unavailable — callers fall back to static templates.
"""
import hashlib
import html
import json
import logging
import re

from django.core.cache import cache

from apps.requests.llm_client import llm
from .prompts import SAFETY_SYSTEM, SCENARIO_PROMPTS, FORBIDDEN_PATTERNS

logger = logging.getLogger(__name__)

CACHE_TTL = 60 * 60 * 24  # 24h


def request_facts(request_obj) -> str:
    """Serialize request facts — the ONLY facts the LLM may use."""
    items = request_obj.items.filter(is_confirmed=True)
    if not items.exists():
        items = request_obj.items.all()
    lines = [f"Позиции заявки RFQ-{request_obj.code}:"]
    for i, item in enumerate(items, 1):
        unit = item.unit.short_name if item.unit else ""
        spec = f" ({item.spec})" if item.spec else ""
        lines.append(f"{i}. {item.name}{spec} — {item.quantity} {unit}")
    address = request_obj.address.address if request_obj.address else "не указан"
    lines.append(f"Адрес доставки: {address}")
    if request_obj.comment:
        lines.append(f"Комментарий заказчика: {request_obj.comment}")
    return "\n".join(lines)


def _cache_key(scenario, request_obj, supplier, context) -> str:
    raw = json.dumps(
        {
            "scenario": scenario,
            "req": [request_obj.id, str(request_obj.updated_at)],
            "sup": [supplier.id if supplier else None],
            "ctx": context or {},
        },
        sort_keys=True,
        ensure_ascii=False,
        default=str,
    )
    return "llm_writer:" + hashlib.sha256(raw.encode()).hexdigest()


def _scan_safety(subject: str, body: str, request_obj) -> tuple[bool, str]:
    """Post-generation safety scan. Returns (needs_review, reason)."""
    text = f"{subject}\n{body}".lower()
    for pattern in FORBIDDEN_PATTERNS:
        if pattern in text:
            return True, f"запрещённая формулировка: «{pattern}»"
    if request_obj is not None:
        code = request_obj.code.lower()
        if code not in text:
            return True, "в письме не указан код заявки"
    if len(subject) > 150 or len(body.strip()) < 20:
        return True, "подозрительная длина письма"
    return False, ""


def text_to_html(body_text: str) -> str:
    """Minimal safe HTML version of plain-text email body."""
    escaped = html.escape(body_text)
    paragraphs = [p.replace("\n", "<br>") for p in escaped.split("\n\n")]
    inner = "".join(f"<p>{p}</p>" for p in paragraphs if p.strip())
    return (
        '<!DOCTYPE html><html lang="ru"><head><meta charset="UTF-8"></head>'
        '<body style="font-family:Arial,sans-serif;line-height:1.5;color:#18181b;">'
        f'<div style="max-width:640px;margin:0 auto;padding:24px;">{inner}</div>'
        "</body></html>"
    )


def generate_email(scenario, request_obj, supplier=None, context=None, timeout=60):
    """Generate an email via LLM. Returns dict or None when LLM unavailable."""
    if scenario not in SCENARIO_PROMPTS:
        raise ValueError(f"Unknown scenario: {scenario}")
    if not llm.api_key:
        logger.info("LLM_API_KEY not set — static template fallback")
        return None

    context = dict(context or {})
    key = _cache_key(scenario, request_obj, supplier, context)
    cached = cache.get(key)
    if cached is not None:
        return cached

    facts = request_facts(request_obj) if request_obj is not None else context.get("request_facts", "")
    from collections import defaultdict
    prompt = SCENARIO_PROMPTS[scenario].format_map(defaultdict(
        str,
        supplier_name=supplier.name if supplier else "поставщик",
        request_code=request_obj.code if request_obj is not None else "",
        request_facts=facts,
        **{k: str(v) for k, v in context.items()},
    ))
    try:
        result = llm.chat(
            [
                {"role": "system", "content": SAFETY_SYSTEM},
                {"role": "user", "content": prompt},
            ],
            timeout=timeout,
        )
        content = result["choices"][0]["message"]["content"].strip()
        content = re.sub(r"^```(?:json)?\s*", "", content)
        content = re.sub(r"\s*```$", "", content)
        data = json.loads(content)
        subject = str(data.get("subject", "")).strip()
        body_text = str(data.get("body_text", "")).strip()
        needs_review = bool(data.get("needs_review", False))
        review_reason = str(data.get("review_reason", "")).strip()
        if not subject or not body_text:
            logger.warning("LLM returned empty subject/body for %s", scenario)
            return None
    except Exception:
        logger.exception("llm_writer failed for scenario %s", scenario)
        return None

    flagged, reason = _scan_safety(subject, body_text, request_obj)
    if flagged:
        needs_review = True
        review_reason = review_reason or reason

    out = {
        "subject": subject,
        "body_text": body_text,
        "body_html": text_to_html(body_text),
        "needs_review": needs_review,
        "review_reason": review_reason,
        "source": "llm",
    }
    cache.set(key, out, CACHE_TTL)
    return out
