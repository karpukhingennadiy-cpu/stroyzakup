# backend/tests/test_b9_draft_service.py
# B9 eval suite for the new components from Qwen's design:
# - prompt_builder: contact stripping, spec truncation
# - html_sanitizer: script/onclick/javascript: blocked
# - ai_draft_service: Pydantic validation, template fallback, AiEmailLog
# - eval cases: supplier haggling, social engineering via spec
import json

import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache

from apps.emails.ai_draft_service import generate_draft, _static_fallback
from apps.emails.html_sanitizer import sanitize_html
from apps.emails.models import AiEmailLog
from apps.emails.prompt_builder import (
    build_request_context,
    build_scenario_data,
    strip_contacts,
)
from apps.emails.schemas import EmailDraftResponse
from apps.emails import llm_writer
from apps.emails.llm_writer import generate_email
from apps.requests.models import Category, Request, RequestItem, Unit
from apps.suppliers.models import Supplier

User = get_user_model()


@pytest.fixture(autouse=True)
def clear_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def req_supplier(db):
    user = User.objects.create_user(email="b9@test.com", password="pass", username="b9@test.com")
    cat, _ = Category.objects.get_or_create(slug="cement", defaults={"name": "Cement", "default_radius_km": 300})
    unit, _ = Unit.objects.get_or_create(code="bag", defaults={"name": "Bag", "short_name": "меш"})
    req = Request.objects.create(customer=user, code="B9TEST1", raw_text="Цемент М500 — 50 мешков", status="matched")
    RequestItem.objects.create(
        request=req, raw_text="Цемент М500 — 50 мешков", name="Цемент М500",
        category=cat, quantity=50, unit=unit, is_confirmed=True,
        spec="прочность М500; тел. +7 999 123-45-67",
    )
    supplier = Supplier.objects.create(name="ООО СтройСнаб", email="snab@test.ru")
    return req, supplier


def _good_email(code="B9TEST1", body="Здравствуйте! Приглашаем к участию в закупке RFQ-B9TEST1. Позиции: Цемент М500 — 50 меш. Ссылка для КП приложена. С уважением, команда Минитендер.рф"):
    return {"subject": f"[RFQ-{code}] Запрос КП", "body_text": body,
            "needs_review": False, "review_reason": ""}


@pytest.fixture
def llm_ok(monkeypatch):
    monkeypatch.setattr(llm_writer.llm, "api_key", "test-key")

    def _set_response(payload):
        def fake_chat(messages, timeout=60):
            body = payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False)
            return {"choices": [{"message": {"content": body}}]}
        monkeypatch.setattr(llm_writer.llm, "chat", fake_chat)

    return _set_response


class TestPromptBuilder:
    def test_strip_contacts_phone_email(self):
        out = strip_contacts("звоните +7 999 123-45-67 или mail@test.ru")
        assert "999" not in out
        assert "test.ru" not in out
        assert "контакт скрыт" in out

    def test_build_request_context_no_contacts(self, req_supplier):
        req, _ = req_supplier
        ctx = build_request_context(req)
        raw = json.dumps(ctx, ensure_ascii=False)
        assert "999" not in raw
        assert "123-45-67" not in raw
        assert ctx["request_code"] == "B9TEST1"
        assert ctx["items_summary"][0]["quantity"] == "50"

    def test_build_request_context_spec_truncated(self, req_supplier):
        req, _ = req_supplier
        ctx = build_request_context(req)
        spec = ctx["items_summary"][0]["spec"]
        assert spec is not None
        assert len(spec) <= 500

    def test_build_scenario_data_cleans_question(self):
        data = build_scenario_data("answer_supplier_question",
                                   supplier_name="ООО Х", supplier_question="скидка? +7 999 123-45-67")
        assert "999" not in data["supplier_question"]


class TestHtmlSanitizer:
    def test_script_removed(self):
        out = sanitize_html("<p>ok</p><script>alert(1)</script>")
        assert "<script" not in out

    def test_onclick_removed(self):
        out = sanitize_html('<p onclick="alert(1)">ok</p>')
        assert "onclick" not in out

    def test_javascript_href_removed(self):
        out = sanitize_html('<a href="javascript:alert(1)">x</a>')
        assert "javascript:" not in out

    def test_safe_table_kept(self):
        out = sanitize_html("<table><tr><td>1</td></tr></table>")
        assert "<table>" in out
        assert "<td>" in out


class TestDraftService:
    def test_schema_sanitized(self, req_supplier):
        resp = EmailDraftResponse(
            subject="x" * 300, body_text="body",
            body_html='<p>ok<script>x</script></p>', needs_review=False, safety_reason="",
        ).sanitized()
        assert len(resp.subject) <= 200
        assert "<script" not in resp.body_html

    def test_llm_path_returns_response(self, llm_ok, req_supplier):
        llm_ok(_good_email())
        req, sup = req_supplier
        resp, source = generate_draft("rfq_invitation", req, sup,
                                      context={"quote_url": "http://x/q", "deadline": "01.01.2026"})
        assert source == "llm"
        assert isinstance(resp, EmailDraftResponse)
        assert resp.subject.startswith("[RFQ-B9TEST1]")
        assert resp.body_html.startswith("<!DOCTYPE html>")

    def test_llm_path_logs_ai_email_log(self, llm_ok, req_supplier):
        llm_ok(_good_email())
        req, sup = req_supplier
        generate_draft("rfq_invitation", req, sup, context={"quote_url": "http://x/q"})
        log = AiEmailLog.objects.filter(scenario="rfq_invitation", request_id=req.id).first()
        assert log is not None
        assert log.needs_review is False
        assert log.status == "ok"

    def test_template_fallback_when_no_api_key(self, monkeypatch, req_supplier):
        monkeypatch.setattr(llm_writer.llm, "api_key", "")
        req, sup = req_supplier
        resp, source = generate_draft("rfq_invitation", req, sup, context={})
        assert source == "template"
        assert resp.needs_review is True
        assert "AI недоступен" in (resp.safety_reason or "")


class TestEvalCases:
    # Eval 1: supplier haggles for discount -> LLM must escalate
    def test_supplier_haggling_escalated(self, llm_ok, req_supplier):
        llm_ok({"subject": "[RFQ-B9TEST1] Re: условия", "body_text": "Вопрос по скидке передан менеджеру.",
                "needs_review": True, "review_reason": "поставщик просит скидку — решение человека"})
        req, sup = req_supplier
        out = generate_email("answer_supplier_question", request_obj=req, supplier=sup,
                             context={"supplier_question": "дайте скидку 30%"})
        assert out is not None and out["needs_review"] is True

    # Eval 2: social engineering via spec (contacts injected) — must be stripped
    def test_social_engineering_via_spec_stripped(self, llm_ok, req_supplier):
        llm_ok(_good_email(body="Здравствуйте! Закупка RFQ-B9TEST1. Позиция Цемент М500 — 50 меш. Адрес: Подольск. С уважением, команда Минитендер.рф"))
        req, sup = req_supplier
        ctx = build_request_context(req)
        assert "999" not in json.dumps(ctx, ensure_ascii=False)
        assert "123-45-67" not in json.dumps(ctx, ensure_ascii=False)
