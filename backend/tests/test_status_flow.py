"""G2: Backend status flow — select_winner (ready) and complete."""
import pytest
from rest_framework.test import APIClient

from apps.quotes.models import Quote, QuoteItem, RfqInvitation
from apps.requests.models import Category, Request, RequestItem, Unit
from apps.suppliers.models import Supplier
from django.contrib.auth import get_user_model

User = get_user_model()


def _client(email, password="pass"):
    User.objects.create_user(email=email, password=password, username=email)
    client = APIClient()
    r = client.post("/api/auth/login/", {"email": email, "password": password})
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {r.data['access']}")
    return client


@pytest.fixture
def owner_client(db):
    return _client("flow-owner@test.com")


@pytest.fixture
def other_client(db):
    return _client("flow-other@test.com")


@pytest.fixture
def request_with_quotes(db, owner_client):
    user = User.objects.get(email="flow-owner@test.com")
    req = Request.objects.create(
        customer=user, code="FLOW01", status="collecting_quotes",
        raw_text="Цемент М500 - 10 меш")
    cat, _ = Category.objects.get_or_create(slug="cement", defaults={"name": "Cement"})
    unit, _ = Unit.objects.get_or_create(code="bag", defaults={"name": "Bag", "short_name": "меш"})
    item = RequestItem.objects.create(
        request=req, raw_text="x", name="Цемент М500",
        category=cat, quantity=10, unit=unit, is_confirmed=True)
    quotes = []
    for name, price, delivery in (("BestSup", 500, 0), ("MidSup", 550, 100)):
        sup = Supplier.objects.create(name=name, email=f"{name.lower()}@sup.ru")
        inv = RfqInvitation.objects.create(
            request=req, supplier=sup, code=name[:8].upper(), reply_code=name.lower(),
            reply_email=f"rfq-{name.lower()}@in.example", quote_token=name.lower() * 8)
        q = Quote.objects.create(
            request=req, supplier=sup, invitation=inv,
            status="received", delivery_cost=delivery,
            delivery_time="3 дня", payment_terms="100% предоплата")
        QuoteItem.objects.create(quote=q, request_item=item, price=price)
        quotes.append(q)
    return req, quotes


class TestSelectWinner:
    def test_select_winner_ok(self, owner_client, request_with_quotes):
        req, quotes = request_with_quotes
        best = quotes[0]
        r = owner_client.post("/api/quotes/select_winner/", {"quote_id": best.id})
        assert r.status_code == 200
        assert r.data["status"] == "ready"
        assert r.data["selected_quote"]["id"] == best.id

        req.refresh_from_db()
        assert req.status == "ready"

        best.refresh_from_db()
        assert best.status == "selected"

        # Other quotes rejected
        for q in quotes[1:]:
            q.refresh_from_db()
            assert q.status == "rejected"

    def test_select_winner_other_users_quote_404(self, other_client, request_with_quotes):
        req, quotes = request_with_quotes
        r = other_client.post("/api/quotes/select_winner/", {"quote_id": quotes[0].id})
        assert r.status_code == 404

    def test_select_winner_missing_quote_id(self, owner_client):
        r = owner_client.post("/api/quotes/select_winner/", {})
        assert r.status_code == 400
        assert "quote_id" in r.data["error"]

    def test_select_winner_invalid_status(self, owner_client, request_with_quotes):
        req, quotes = request_with_quotes
        req.status = "completed"
        req.save(update_fields=["status"])
        r = owner_client.post("/api/quotes/select_winner/", {"quote_id": quotes[0].id})
        assert r.status_code == 400
        assert "Cannot select winner" in r.data["error"]


class TestCompleteRequest:
    def test_complete_ok(self, owner_client, request_with_quotes):
        req, quotes = request_with_quotes
        # Precondition: request must be in ready status
        req.status = "ready"
        req.save(update_fields=["status"])

        r = owner_client.post(f"/api/requests/{req.id}/complete/")
        assert r.status_code == 200
        assert r.data["status"] == "completed"

        req.refresh_from_db()
        assert req.status == "completed"

    def test_complete_wrong_status(self, owner_client, request_with_quotes):
        req, quotes = request_with_quotes
        # Status is collecting_quotes, not ready
        r = owner_client.post(f"/api/requests/{req.id}/complete/")
        assert r.status_code == 400
        assert "Cannot complete" in r.data["error"]

    def test_complete_other_users_request_404(self, other_client, request_with_quotes):
        req, quotes = request_with_quotes
        req.status = "ready"
        req.save(update_fields=["status"])
        r = other_client.post(f"/api/requests/{req.id}/complete/")
        assert r.status_code == 404
