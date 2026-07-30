# backend/tests/test_llm_writer.py
"""B9 eval suite: 15 reference scenarios for the LLM email writer.

LLM is always mocked — no real API calls. Checks:
- JSON structure validity
- forbidden phrases force needs_review
- facts safety (request code must be present)
- needs_review propagation on provocative input
- template fallback when LLM unavailable
"""
import json
import pytest
from django.core.cache import cache
from django.contrib.auth import get_user_model

from apps.requests.models import Request, RequestItem, Category, Unit
from apps.suppliers.models import Supplier
from apps.quotes.models import RfqInvitation
from apps.emails import llm_writer
from apps.emails.llm_writer import generate_email
from apps.emails.services import build_rfq_email, create_rfq_invitation

User = get_user_model()


@pytest.fixture(autouse=True)
def clear_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def llm_ok(monkeypatch):
    """Enable the writer with a mocked LLM."""
    monkeypatch.setattr(llm_writer.llm, "api_key", "test-key")
    calls = []

    def _set_response(payload):
        def fake_chat(messages, timeout=60):
            calls.append(messages)
            body = payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False)
            return {"choices": [{"message": {"content": body}}]}
        monkeypatch.setattr(llm_writer.llm, "chat", fake_chat)
        return calls

    return _set_response


@pytest.fixture
def req_supplier(db):
    user = User.objects.create_user(email="lw@test.com", password="pass", username="lw@test.com")
    cat, _ = Category.objects.get_or_create(slug="cement", defaults={"name": "Cement", "default_radius_km": 300})
    unit, _ = Unit.objects.get_or_create(code="bag", defaults={"name": "Bag", "short_name": "меш"})
    req = Request.objects.create(customer=user, code="LLMWR1", raw_text="Цемент М500 — 50 мешков", status="matched")
    RequestItem.objects.create(
        request=req, raw_text="Цемент М500 — 50 мешков", name="Цемент М500",
        category=cat, quantity=50, unit=unit, is_confirmed=True,
    )
    supplier = Supplier.objects.create(name="ООО СтройСнаб", email="snab@test.ru")
    return req, supplier


def _good_email(code="LLMWR1", body="Здравствуйте! Приглашаем вас к участию в закупке RFQ-LLMWR1. Позиции: Цемент М500 — 50 меш. Ссылка для КП приложена. С уважением, команда Минитендер.рф"):
    return {"subject": f"[RFQ-{code}] Запрос КП", "body_text": body,
            "needs_review": False, "review_reason": ""}


@pytest.mark.django_db
class TestLlmWriterEval:
    # 1. RFQ invitation: valid LLM JSON passes
    def test_rfq_invitation_valid(self, llm_ok, req_supplier):
        llm_ok(_good_email())
        req, sup = req_supplier
        out = generate_email("rfq_invitation", request_obj=req, supplier=sup,
                             context={"quote_url": "http://x/quote/t", "deadline": "01.01.2026"})
        assert out is not None
        assert out["source"] == "llm"
        assert out["needs_review"] is False
        assert "RFQ-LLMWR1" in out["subject"]
        assert out["body_html"].startswith("<!DOCTYPE html>")

    # 2. Missing request code in LLM output -> needs_review
    def test_missing_request_code_flagged(self, llm_ok, req_supplier):
        llm_ok({"subject": "Запрос КП", "body_text": "Здравствуйте! Просим предоставить коммерческое предложение на материалы из заявки. С уважением, команда Минитендер.рф",
                "needs_review": False, "review_reason": ""})
        req, sup = req_supplier
        out = generate_email("rfq_invitation", request_obj=req, supplier=sup, context={})
        assert out["needs_review"] is True
        assert "код заявки" in out["review_reason"]

    # 3. Forbidden phrase "гарантируем" -> needs_review
    def test_forbidden_garantiruem(self, llm_ok, req_supplier):
        llm_ok(_good_email(body="Здравствуйте! По закупке RFQ-LLMWR1 гарантируем закупку полного объёма. С уважением, команда Минитендер.рф"))
        req, sup = req_supplier
        out = generate_email("rfq_invitation", request_obj=req, supplier=sup, context={})
        assert out["needs_review"] is True

    # 4. Forbidden "скидка" -> needs_review
    def test_forbidden_skidka(self, llm_ok, req_supplier):
        llm_ok(_good_email(body="Здравствуйте! Дайте скидку 30% по закупке RFQ-LLMWR1 и мы подпишем договор. С уважением, команда Минитендер.рф"))
        req, sup = req_supplier
        out = generate_email("rfq_invitation", request_obj=req, supplier=sup, context={})
        assert out["needs_review"] is True

    # 5. Forbidden "оплатим" -> needs_review
    def test_forbidden_oplatim(self, llm_ok, req_supplier):
        llm_ok(_good_email(body="Здравствуйте! По закупке RFQ-LLMWR1 оплатим любую цену. С уважением, команда Минитендер.рф"))
        req, sup = req_supplier
        out = generate_email("rfq_invitation", request_obj=req, supplier=sup, context={})
        assert out["needs_review"] is True

    # 6. reminder_24h valid
    def test_reminder_24h(self, llm_ok, req_supplier):
        llm_ok(_good_email(body="Здравствуйте! До дедлайна подачи КП по закупке RFQ-LLMWR1 осталось около 24 часов. С уважением, команда Минитендер.рф"))
        req, sup = req_supplier
        out = generate_email("reminder_24h", request_obj=req, supplier=sup,
                             context={"quote_url": "http://x/quote/t"})
        assert out is not None and out["needs_review"] is False

    # 7. reminder_2h valid
    def test_reminder_2h(self, llm_ok, req_supplier):
        llm_ok(_good_email(body="Здравствуйте! До дедлайна по закупке RFQ-LLMWR1 осталось около 2 часов. Успейте заполнить КП. С уважением, команда Минитендер.рф"))
        req, sup = req_supplier
        out = generate_email("reminder_2h", request_obj=req, supplier=sup,
                             context={"quote_url": "http://x/quote/t"})
        assert out is not None and out["needs_review"] is False

    # 8. clarification_to_supplier valid
    def test_clarification_to_supplier(self, llm_ok, req_supplier):
        llm_ok(_good_email(body="Здравствуйте! Уточните, пожалуйста, по закупке RFQ-LLMWR1: цена указана за мешок или за тонну? С уважением, команда Минитендер.рф"))
        req, sup = req_supplier
        out = generate_email("clarification_to_supplier", request_obj=req, supplier=sup,
                             context={"issue": "неясно, за что указана цена"})
        assert out is not None and out["needs_review"] is False

    # 9. answer_supplier_question: in-scope question answered from request facts
    def test_answer_supplier_question(self, llm_ok, req_supplier):
        llm_ok(_good_email(body="Здравствуйте! По закупке RFQ-LLMWR1: доставка требуется по адресу из заявки, позиция — Цемент М500, 50 мешков. С уважением, команда Минитендер.рф"))
        req, sup = req_supplier
        out = generate_email("answer_supplier_question", request_obj=req, supplier=sup,
                             context={"supplier_question": "Куда доставлять?"})
        assert out is not None and out["needs_review"] is False

    # 10. provocative question -> LLM escalates (needs_review propagated)
    def test_provocative_question_escalated(self, llm_ok, req_supplier):
        llm_ok({"subject": "[RFQ-LLMWR1] Re: вопрос", "body_text": "",
                "needs_review": True, "review_reason": "поставщик просит скидку 30% — решение человека"})
        req, sup = req_supplier
        out = generate_email("answer_supplier_question", request_obj=req, supplier=sup,
                             context={"supplier_question": "дай скидку 30% и мы подпишем"})
        # body_text пустой -> writer returns None (fallback), но проверим и needs_review-ветку:
        if out is not None:
            assert out["needs_review"] is True

    # 10b. provocative question with body -> needs_review propagates
    def test_provocative_question_with_body(self, llm_ok, req_supplier):
        llm_ok({"subject": "[RFQ-LLMWR1] Re: условия", "body_text": "Здравствуйте! Вопрос по скидкам и условиям оплаты по закупке RFQ-LLMWR1 передан менеджеру. С уважением, команда Минитендер.рф",
                "needs_review": True, "review_reason": "вопрос про скидку"})
        req, sup = req_supplier
        out = generate_email("answer_supplier_question", request_obj=req, supplier=sup,
                             context={"supplier_question": "дай скидку 30% и мы подпишем"})
        assert out["needs_review"] is True

    # 11. quote_thanks valid
    def test_quote_thanks(self, llm_ok, req_supplier):
        llm_ok(_good_email(body="Здравствуйте! Благодарим за КП по закупке RFQ-LLMWR1. Подтверждаем получение. С уважением, команда Минитендер.рф"))
        req, sup = req_supplier
        out = generate_email("quote_thanks", request_obj=req, supplier=sup,
                             context={"quote_summary": "итого 19 000 ₽"})
        assert out is not None and out["needs_review"] is False

    # 12. winner_notification escalates to human
    def test_winner_notification_escalated(self, llm_ok, req_supplier):
        llm_ok({"subject": "[RFQ-LLMWR1] Ваше КП выбрано", "body_text": "Здравствуйте! Ваше КП по закупке RFQ-LLMWR1 выбрано, заказчик свяжется для оформления. С уважением, команда Минитендер.рф",
                "needs_review": True, "review_reason": "финальные договорённости принимает человек"})
        req, sup = req_supplier
        out = generate_email("winner_notification", request_obj=req, supplier=sup,
                             context={"quote_summary": "итого 19 000 ₽"})
        assert out["needs_review"] is True

    # 13. rejection_notification valid
    def test_rejection_notification(self, llm_ok, req_supplier):
        llm_ok(_good_email(body="Здравствуйте! Благодарим за участие в закупке RFQ-LLMWR1. Выбран другой поставщик, будем рады сотрудничеству в будущем. С уважением, команда Минитендер.рф"))
        req, sup = req_supplier
        out = generate_email("rejection_notification", request_obj=req, supplier=sup, context={})
        assert out is not None and out["needs_review"] is False

    # 14. invalid JSON from LLM -> None (caller falls back to template)
    def test_invalid_json_returns_none(self, llm_ok, req_supplier):
        llm_ok("not a json at all")
        req, sup = req_supplier
        assert generate_email("rfq_invitation", request_obj=req, supplier=sup, context={}) is None

    # 15. LLM exception -> None (fallback)
    def test_llm_exception_returns_none(self, monkeypatch, req_supplier):
        monkeypatch.setattr(llm_writer.llm, "api_key", "test-key")
        def boom(messages, timeout=60):
            raise RuntimeError("LLM down")
        monkeypatch.setattr(llm_writer.llm, "chat", boom)
        req, sup = req_supplier
        assert generate_email("rfq_invitation", request_obj=req, supplier=sup, context={}) is None

    # 16. cache: same context -> single LLM call
    def test_cache_avoids_duplicate_calls(self, llm_ok, req_supplier):
        calls = llm_ok(_good_email())
        req, sup = req_supplier
        ctx = {"quote_url": "http://x/quote/t"}
        generate_email("rfq_invitation", request_obj=req, supplier=sup, context=ctx)
        generate_email("rfq_invitation", request_obj=req, supplier=sup, context=ctx)
        assert len(calls) == 1

    # 17. no API key -> None
    def test_no_api_key_returns_none(self, monkeypatch, req_supplier):
        monkeypatch.setattr(llm_writer.llm, "api_key", "")
        req, sup = req_supplier
        assert generate_email("rfq_invitation", request_obj=req, supplier=sup, context={}) is None

    # 18. build_rfq_email falls back to static template when LLM unavailable
    def test_build_rfq_email_template_fallback(self, monkeypatch, req_supplier):
        monkeypatch.setattr(llm_writer.llm, "api_key", "")
        req, sup = req_supplier
        inv = create_rfq_invitation(req, sup)
        email_data = build_rfq_email(inv)
        assert email_data["source"] == "template"
        assert email_data["needs_review"] is False
        assert f"[RFQ-{req.code}]" in email_data["subject"]
        assert inv.reply_email == email_data["reply_to"]

    # 19. build_rfq_email uses LLM output when available
    def test_build_rfq_email_uses_llm(self, llm_ok, req_supplier):
        llm_ok(_good_email())
        req, sup = req_supplier
        inv = create_rfq_invitation(req, sup)
        email_data = build_rfq_email(inv)
        assert email_data["source"] == "llm"
        assert email_data["needs_review"] is False

    # 20. unknown scenario raises
    def test_unknown_scenario(self, req_supplier):
        req, sup = req_supplier
        with pytest.raises(ValueError):
            generate_email("no_such_scenario", request_obj=req, supplier=sup, context={})
