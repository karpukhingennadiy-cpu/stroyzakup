# backend/apps/emails/llm_writer.py
# LLM email writer (B9).
#
# generate_email(scenario, request_obj, supplier, context) ->
#     {"subject", "body_text", "body_html", "needs_review", "review_reason", "source"}
#
# - JSON-validated LLM output via Pydantic EmailDraftResponse, cached by context hash.
# - Post-generation safety scan: forbidden phrases or missing request code
#   force needs_review=True.
# - Returns None when LLM is unavailable — callers fall back to static templates.
# - Every call is logged to AiEmailLog for debugging/eval.
import hashlib
import html
import json
import logging
import re
import time

from django.core.cache import cache
from pydantic import ValidationError

from apps.requests.llm_client import llm
from .prompts import SAFETY_SYSTEM, SCENARIO_PROMPTS, FORBIDDEN_PATTERNS
from .schemas import EmailDraftResponse

logger = logging.getLogger(__name__)

CACHE_TTL = 60 * 60  # 1h: request data can change (B9)
MAX_RETRIES = 3      # B9: 3 invalid JSON attempts -> fallback
BT = chr(96) * 3     # triple backtick for markdown fence stripping


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
    return chr(10).join(lines)


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


def _scan_safety(subject: str, body: str, request_obj, scenario: str = "") -> tuple[bool, str]:
    """Post-generation safety scan. Returns (needs_review, reason)."""
    text = f"{subject}" + chr(10) + f"{body}"
    text = text.lower()
    for pattern in FORBIDDEN_PATTERNS:
        if pattern in text:
            return True, f"запрещённая формулировка: «{pattern}»"
    if request_obj is not None:
        code = request_obj.code.lower()
        if code not in text:
            return True, "в письме не указан код заявки"
        # Fact completeness for invitations: every request item must be
        # mentioned — the LLM must not silently drop positions (E2E finding)
        if scenario == "rfq_invitation":
            body_norm = re.sub(r"\s+", " ", body.lower())
            items = request_obj.items.filter(is_confirmed=True)
            if not items.exists():
                items = request_obj.items.all()
            for item in items:
                name = re.sub(r"\s+", " ", (item.name or "").lower()).strip()
                if not name or len(name) < 4:
                    continue
                if name in body_norm:
                    continue
                # Tolerant check: first two tokens of the item name must appear
                tokens = [t for t in name.split(" ") if len(t) >= 2][:2]
                if tokens and all(t in body_norm for t in tokens):
                    continue
                return True, f"в письме потеряна позиция заявки: «{item.name}»"
    if len(subject) > 150 or len(body.strip()) < 20:
        return True, "подозрительная длина письма"
    return False, ""


def text_to_html(body_text: str) -> str:
    """Minimal safe HTML version of plain-text email body."""
    escaped = html.escape(body_text)
    paragraphs = [p.replace(chr(10), "<br>") for p in escaped.split(chr(10) * 2)]
    inner = "".join(f"<p>{p}</p>" for p in paragraphs if p.strip())
    return (
        '<!DOCTYPE html><html lang="ru"><head><meta charset="UTF-8"></head>'
        '<body style="font-family:Arial,sans-serif;line-height:1.5;color:#18181b;">'
        f'<div style="max-width:640px;margin:0 auto;padding:24px;">{inner}</div>'
        "</body></html>"
    )


def _parse_llm_json(content: str) -> EmailDraftResponse | None:
    """Parse LLM output into EmailDraftResponse. Returns None on failure."""
    content = content.strip()
    content = re.sub(r"^" + BT + r"(?:json)?\s*", "", content)
    content = re.sub(r"\s*" + BT + r"$", "", content)
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return None
    # Backward compat: old field name review_reason -> safety_reason
    if "review_reason" in data and "safety_reason" not in data:
        data["safety_reason"] = data.pop("review_reason")
    try:
        return EmailDraftResponse(**data).sanitized()
    except ValidationError:
        return None


def _log_call(scenario, request_id, prompt_text, response_text,
              needs_review, safety_reason, latency_ms, status, source):
    """Persist one LLM call for debugging/eval (B9). Failures are non-fatal."""
    try:
        from .models import AiEmailLog
        AiEmailLog.objects.create(
            scenario=scenario,
            request_id=request_id,
            prompt_preview=(prompt_text or "")[:4000],
            response_preview=(response_text or "")[:4000],
            needs_review=bool(needs_review),
            safety_reason=(safety_reason or "")[:1000],
            latency_ms=int(latency_ms or 0),
            status=status[:20],
            source=source[:20],
        )
    except Exception:
        logger.exception("AiEmailLog write failed")


def generate_email(scenario, request_obj, supplier=None, context=None, timeout=60):
    """Generate an email via LLM. Returns dict or None when LLM unavailable.

    Retries up to MAX_RETRIES on invalid JSON. Logs every attempt to
    AiEmailLog. Returns None only when LLM itself is unavailable or after
    repeated invalid output — callers then use static templates.
    """
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

    last_error = ""
    for attempt in range(MAX_RETRIES):
        start = time.monotonic()
        try:
            result = llm.chat(
                [
                    {"role": "system", "content": SAFETY_SYSTEM},
                    {"role": "user", "content": prompt},
                ],
                timeout=timeout,
            )
            raw = result["choices"][0]["message"]["content"].strip()
            parsed = _parse_llm_json(raw)
            latency = int((time.monotonic() - start) * 1000)
            if parsed is None:
                last_error = "invalid_json"
                _log_call(scenario, request_obj.id if request_obj else None,
                          prompt, raw, False, "", latency, "error", "llm")
                logger.warning("llm_writer invalid JSON (attempt %d) for %s", attempt + 1, scenario)
                continue
        except Exception as exc:
            latency = int((time.monotonic() - start) * 1000)
            last_error = str(exc)[:200]
            _log_call(scenario, request_obj.id if request_obj else None,
                      prompt, "", False, "", latency, "error", "llm")
            logger.exception("llm_writer LLM call failed for %s", scenario)
            return None  # LLM unavailable — caller falls back to template

        subject = parsed.subject
        body_text = parsed.body_text
        body_html = parsed.body_html or text_to_html(body_text)
        needs_review = parsed.needs_review
        safety_reason = parsed.safety_reason

        if not subject or not body_text:
            last_error = "empty_subject_body"
            _log_call(scenario, request_obj.id if request_obj else None,
                      prompt, raw, False, "", latency, "error", "llm")
            continue

        flagged, reason = _scan_safety(subject, body_text, request_obj, scenario)
        if flagged:
            needs_review = True
            safety_reason = safety_reason or reason

        out = {
            "subject": subject,
            "body_text": body_text,
            "body_html": body_html,
            "needs_review": needs_review,
            "review_reason": safety_reason or "",
            "source": "llm",
        }
        cache.set(key, out, CACHE_TTL)
        _log_call(scenario, request_obj.id if request_obj else None,
                  prompt, raw, needs_review, safety_reason, latency, "ok", "llm")
        return out

    logger.warning("llm_writer exhausted retries for %s: %s", scenario, last_error)
    return None
