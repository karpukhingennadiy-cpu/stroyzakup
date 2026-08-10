# backend/apps/emails/schemas.py
# Unified LLM response schema for all email scenarios (B9).
# Single Pydantic model that every LLM call must satisfy. Forces structured
# output (DeepSeek JSON mode / function calling) instead of regex parsing.
from pydantic import BaseModel, Field


class EmailDraftResponse(BaseModel):
    # Единая схема ответа LLM для всех сценариев переписки.
    subject: str = Field('', description='Тема письма (обрезается до 200 в sanitized)')
    body_text: str = Field(..., description='Plain text версия тела письма')
    body_html: str = Field('', description='HTML версия тела письма (inline-стили, whitelist тегов). Пусто — сгенерируется из body_text')

    needs_review: bool = Field(
        False,
        description='TRUE если запрос выходит за рамки фактов заявки, содержит обещания или требует решения человека',
    )
    safety_reason: str | None = Field(
        None,
        description='Если needs_review=True, здесь ОБЯЗАТЕЛЬНО причина на русском',
    )

    def sanitized(self):
        # Post-parse guard: enforce max lengths and whitelist HTML tags.
        from .html_sanitizer import sanitize_html

        subject = (self.subject or '').strip()[:200]
        body_text = (self.body_text or '').strip()
        body_html = sanitize_html(self.body_html or '')
        return EmailDraftResponse(
            subject=subject,
            body_text=body_text,
            body_html=body_html,
            needs_review=bool(self.needs_review),
            safety_reason=(self.safety_reason or '').strip()[:1000] or None,
        )
