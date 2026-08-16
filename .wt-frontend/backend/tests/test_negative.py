# backend/tests/test_negative.py
"""A2: negative-branch API coverage. LLM and geocoder are always mocked —
no real external API calls."""
import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework.test import APIClient

from apps.requests.models import Request, RequestItem, Category, Unit, Address
from apps.requests.llm_client import llm
from apps.suppliers.models import Supplier, SupplierCategory
from apps.quotes.models import RfqInvitation, Quote, QuoteItem

User = get_user_model()


def make_client(email="neg@test.com"):
    User.objects.create_user(email=email, password="pass", username=email)
    client = APIClient()
    r = client.post("/api/auth/login/", {"email": email, "password": "pass"})
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {r.data['access']}")
    return client


@pytest.fixture
def client_a():
    return make_client("nega@test.com")


@pytest.fixture
def client_b():
    return make_client("negb@test.com")


@pytest.fixture(autouse=True)
def no_llm(monkeypatch):
    """Force the regex fallback parser — zero external calls in tests."""
    monkeypatch.setattr(llm, "api_key", "")


@pytest.fixture
def catalog(db):
    cat, _ = Category.objects.get_or_create(
        slug="cement", defaults={"name": "Cement", "default_radius_km": 300})
    Unit.objects.get_or_create(code="bag", defaults={"name": "Bag", "short_name": "меш"})
    Unit.objects.get_or_create(code="sht", defaults={"name": "Piece", "short_name": "шт"})
    return cat


def create_request(client, raw_text="Цемент М500 - 50 меш"):
    r = client.post("/api/requests/", {"raw_text": raw_text})
    assert r.status_code == 201
    return r.data["id"]


@pytest.mark.django_db
class TestParseNegative:
    def test_parse_other_users_request_404(self, client_a, client_b):
        req_id = create_request(client_a)
        r = client_b.post(f"/api/requests/{req_id}/parse/")
        assert r.status_code == 404

    def test_parse_empty_raw_text_422(self, client_a):
        req_id = create_request(client_a, raw_text="")
        r = client_a.post(f"/api/requests/{req_id}/parse/")
        assert r.status_code == 422

    def test_parse_twice_no_duplicates(self, client_a):
        req_id = create_request(client_a, "Цемент М500 - 50 меш\nКирпич - 100 шт")
        r1 = client_a.post(f"/api/requests/{req_id}/parse/")
        assert r1.status_code == 200
        count1 = len(r1.data["items"])
        # back to draft, parse again — diff-update must not duplicate items
        Request.objects.filter(id=req_id).update(status="draft")
        r2 = client_a.post(f"/api/requests/{req_id}/parse/")
        assert r2.status_code == 200
        assert len(r2.data["items"]) == count1
        assert RequestItem.objects.filter(request_id=req_id).count() == count1

    def test_parse_garbage_text(self, client_a):
        req_id = create_request(client_a, "asdf 123")
        r = client_a.post(f"/api/requests/{req_id}/parse/")
        # fallback parser produces a low-confidence item or a clean error — never 500
        assert r.status_code in (200, 422)


@pytest.mark.django_db
class TestMatchNegative:
    def test_match_without_address(self, client_a, catalog):
        req_id = create_request(client_a)
        client_a.post(f"/api/requests/{req_id}/parse/")
        r = client_a.post(f"/api/requests/{req_id}/match_suppliers/")
        assert r.status_code == 200
        assert r.data["status"] == "matched"

    def test_match_limit_5(self, client_a, catalog):
        user = User.objects.get(email="nega@test.com")
        req = Request.objects.create(customer=user, code="LIM001", raw_text="x", status="confirmed")
        RequestItem.objects.create(request=req, raw_text="цемент", name="Цемент",
                                   category=catalog, quantity=1, is_confirmed=True)
        for i in range(8):
            s = Supplier.objects.create(name=f"Sup{i}", email=f"s{i}@t.ru",
                                        moderation_status="verified")
            SupplierCategory.objects.create(supplier=s, category=catalog)
        r = client_a.post(f"/api/requests/{req.id}/match_suppliers/", {"limit": 5})
        assert r.status_code == 200
        assert len(r.data["suppliers"]) <= 5

    def test_match_excludes_rejected_supplier(self, client_a, catalog):
        user = User.objects.get(email="nega@test.com")
        req = Request.objects.create(customer=user, code="MOD001", raw_text="x", status="confirmed")
        RequestItem.objects.create(request=req, raw_text="цемент", name="Цемент",
                                   category=catalog, quantity=1, is_confirmed=True)
        rejected = Supplier.objects.create(name="RejectedSup", email="r@t.ru",
                                           moderation_status="rejected")
        SupplierCategory.objects.create(supplier=rejected, category=catalog)
        verified = Supplier.objects.create(name="OkSup", email="ok@t.ru",
                                           moderation_status="verified")
        SupplierCategory.objects.create(supplier=verified, category=catalog)
        r = client_a.post(f"/api/requests/{req.id}/match_suppliers/")
        names = [s["name"] for s in r.data["suppliers"]]
        assert "RejectedSup" not in names
        assert "OkSup" in names


@pytest.mark.django_db
class TestSendRfqNegative:
    def _setup(self, client, **supplier_kwargs):
        req_id = create_request(client)
        client.post(f"/api/requests/{req_id}/parse/")
        client.post(f"/api/requests/{req_id}/match_suppliers/")
        defaults = {"name": "NoEmailSup", "email": ""}
        defaults.update(supplier_kwargs)
        sup = Supplier.objects.create(**defaults)
        return req_id, sup

    def test_empty_supplier_ids_400(self, client_a):
        req_id = create_request(client_a)
        client_a.post(f"/api/requests/{req_id}/parse/")
        client_a.post(f"/api/requests/{req_id}/match_suppliers/")
        r = client_a.post(f"/api/requests/{req_id}/send_rfq/", {"supplier_ids": []}, format="json")
        assert r.status_code == 400

    def test_nonexistent_supplier_ids(self, client_a):
        req_id = create_request(client_a)
        client_a.post(f"/api/requests/{req_id}/parse/")
        client_a.post(f"/api/requests/{req_id}/match_suppliers/")
        r = client_a.post(f"/api/requests/{req_id}/send_rfq/", {"supplier_ids": [999999]}, format="json")
        assert r.status_code == 200
        assert all(x["status"] != "sent" for x in r.data["results"])
        assert r.data["status"] == "rfq_failed"

    def test_supplier_without_email_skipped(self, client_a):
        req_id, sup = self._setup(client_a)
        r = client_a.post(f"/api/requests/{req_id}/send_rfq/", {"supplier_ids": [sup.id]}, format="json")
        assert r.status_code == 200
        assert r.data["results"][0]["status"] == "skipped"

    def test_repeat_send_rfq_does_not_break(self, client_a):
        req_id, sup = self._setup(client_a, email="repeat@t.ru")
        Request.objects.filter(id=req_id).update(status="matched")
        r1 = client_a.post(f"/api/requests/{req_id}/send_rfq/", {"supplier_ids": [sup.id]}, format="json")
        assert r1.status_code == 200
        r2 = client_a.post(f"/api/requests/{req_id}/send_rfq/", {"supplier_ids": [sup.id]}, format="json")
        assert r2.status_code == 200


@pytest.mark.django_db
class TestPublicQuoteNegative:
    @pytest.fixture
    def invitation(self, db):
        user = User.objects.create_user(email="pq@test.com", password="p", username="pq@test.com")
        cat, _ = Category.objects.get_or_create(slug="cement", defaults={"name": "Cement"})
        unit, _ = Unit.objects.get_or_create(code="bag", defaults={"name": "Bag", "short_name": "меш"})
        req = Request.objects.create(customer=user, code="PUB001", raw_text="x", status="rfq_sent")
        item = RequestItem.objects.create(request=req, raw_text="цемент", name="Цемент М500",
                                          category=cat, quantity=50, unit=unit, is_confirmed=True)
        sup = Supplier.objects.create(name="PubSup", email="pub@t.ru")
        from apps.emails.services import create_rfq_invitation
        inv = create_rfq_invitation(req, sup)
        return inv, item

    def test_invalid_token_404(self, db):
        client = APIClient()
        r = client.get("/api/public/quote/no-such-token/")
        assert r.status_code == 404

    def test_post_price_zero_400(self, invitation):
        inv, item = invitation
        client = APIClient()
        r = client.post(f"/api/public/quote/{inv.quote_token}/",
                        {"items": [{"request_item_id": item.id, "price": 0}]}, format="json")
        assert r.status_code == 400

    def test_post_negative_price_400(self, invitation):
        inv, item = invitation
        client = APIClient()
        r = client.post(f"/api/public/quote/{inv.quote_token}/",
                        {"items": [{"request_item_id": item.id, "price": -100}]}, format="json")
        assert r.status_code == 400

    def test_post_without_items_400(self, invitation):
        inv, _ = invitation
        client = APIClient()
        r = client.post(f"/api/public/quote/{inv.quote_token}/", {}, format="json")
        assert r.status_code == 400

    def test_post_price_not_a_number_400(self, invitation):
        inv, item = invitation
        client = APIClient()
        r = client.post(f"/api/public/quote/{inv.quote_token}/",
                        {"items": [{"request_item_id": item.id, "price": "abc"}]}, format="json")
        assert r.status_code == 400

    def test_no_customer_data_leak(self, invitation):
        inv, _ = invitation
        client = APIClient()
        r = client.get(f"/api/public/quote/{inv.quote_token}/")
        assert r.status_code == 200
        body = str(r.data)
        assert "pq@test.com" not in body  # customer email must not leak

    def test_throttle_429_after_30(self, invitation):
        inv, _ = invitation
        cache.clear()
        client = APIClient()
        last = None
        for i in range(31):
            last = client.get(f"/api/public/quote/{inv.quote_token}/")
        assert last.status_code == 429
        cache.clear()


@pytest.mark.django_db
class TestCompetitiveSheetNegative:
    def test_without_request_id_400(self, client_a):
        r = client_a.get("/api/quotes/competitive_sheet/")
        assert r.status_code == 400

    def test_nonexistent_request_404(self, client_a):
        r = client_a.get("/api/quotes/competitive_sheet/?request_id=999999")
        assert r.status_code == 404

    def test_other_users_request_404(self, client_a, client_b):
        req_id = create_request(client_a)
        r = client_b.get(f"/api/quotes/competitive_sheet/?request_id={req_id}")
        assert r.status_code == 404


@pytest.mark.django_db
class TestQuotesIdor:
    def test_list_quotes_scoped_to_owner(self, client_a, client_b):
        # quotes of user A are invisible in user B's list
        user_a = User.objects.get(email="nega@test.com")
        req = Request.objects.create(customer=user_a, code="IDR001", raw_text="x")
        sup = Supplier.objects.create(name="IdrSup", email="i@t.ru")
        Quote.objects.create(request=req, supplier=sup)
        r = client_b.get("/api/quotes/")
        assert r.status_code == 200
        results = r.data.get("results", r.data)
        assert all(q.get("request") != req.id for q in results)
        r2 = client_b.get(f"/api/quotes/?request_id={req.id}")
        assert r2.data.get("count", len(r2.data.get("results", []))) == 0


@pytest.mark.django_db
class TestGeocodeNegative:
    def test_empty_address_400(self, client_a):
        r = client_a.post("/api/auth/geocode/", {"address": ""})
        assert r.status_code == 400

    def test_geocoder_failure_400(self, client_a, monkeypatch):
        from apps.requests.services import geocoder
        monkeypatch.setattr(geocoder, "geocode", lambda q: None)
        r = client_a.post("/api/auth/geocode/", {"address": "Несуществующий город 999"})
        assert r.status_code == 400


@pytest.mark.django_db
class TestInjectionResilience:
    def test_sqli_in_raw_text(self, client_a):
        r = client_a.post("/api/requests/", {"raw_text": "' OR 1=1--"})
        assert r.status_code == 201
        assert client_a.get("/api/requests/").status_code == 200

    def test_xss_in_raw_text_stored_literally(self, client_a):
        payload = "<script>alert(1)</script>"
        r = client_a.post("/api/requests/", {"raw_text": payload})
        assert r.status_code == 201
        detail = client_a.get(f"/api/requests/{r.data['id']}/")
        assert detail.data["raw_text"] == payload  # stored; React escapes on render

    def test_xss_escaped_in_email_html(self, client_a, db):
        from apps.emails.services import build_rfq_email, create_rfq_invitation
        user = User.objects.get(email="nega@test.com")
        cat, _ = Category.objects.get_or_create(slug="cement", defaults={"name": "Cement"})
        unit, _ = Unit.objects.get_or_create(code="sht", defaults={"name": "Piece", "short_name": "шт"})
        req = Request.objects.create(customer=user, code="XSS001", raw_text="x", status="matched")
        RequestItem.objects.create(
            request=req, raw_text="x", name='<script>alert("x")</script>',
            category=cat, quantity=1, unit=unit, is_confirmed=True)
        sup = Supplier.objects.create(name="XssSup<b>", email="x@t.ru")
        inv = create_rfq_invitation(req, sup)
        email_data = build_rfq_email(inv)
        assert "<script>" not in email_data["body_html"]
        assert "&lt;script&gt;" in email_data["body_html"]
