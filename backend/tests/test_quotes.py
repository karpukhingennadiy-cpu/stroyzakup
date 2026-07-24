import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from apps.requests.models import Request, RequestItem, Category, Unit
from apps.suppliers.models import Supplier
from apps.quotes.models import Quote, QuoteItem, RfqInvitation

User = get_user_model()


@pytest.fixture
def api_client():
    user = User.objects.create_user(
        email="qt@test.com", password="pass", username="qt@test.com"
    )
    client = APIClient()
    r = client.post("/api/auth/login/", {"email": "qt@test.com", "password": "pass"})
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {r.data["access"]}')
    return user, client


@pytest.fixture
def seed_quotes(api_client):
    user, client = api_client
    cat = Category.objects.get_or_create(slug="keram", defaults={"name": "Ceramics"})[0]
    unit = Unit.objects.get_or_create(code="m2", defaults={"name": "sqm", "short_name": "m2"})[0]

    supplier = Supplier.objects.create(name="TestSup", email="sup@q.com")
    req = Request.objects.create(
        customer=user, code="TEST01", raw_text="Tile 100m2", status="confirmed"
    )
    RequestItem.objects.create(
        request=req, raw_text="Tile 100m2", name="Tile", category=cat,
        quantity=100, unit=unit, is_confirmed=True
    )

    invitation = RfqInvitation.objects.create(
        request=req, supplier=supplier,
        code="INV01", reply_email="rfq-TEST01-abc@in.stroyzakup.ru",
        quote_token="token123", status="sent"
    )

    quote = Quote.objects.create(
        request=req, supplier=supplier, invitation=invitation,
        status="received", delivery_cost=5000, payment_terms="50% prepay"
    )
    QuoteItem.objects.create(
        quote=quote, request_item=req.items.first(),
        price=850, vat_included=True
    )

    return req, supplier, quote


@pytest.mark.django_db
class TestQuotes:
    def test_list_quotes(self, api_client, seed_quotes):
        _, client = api_client
        req, _, _ = seed_quotes
        r = client.get(f"/api/quotes/?request_id={req.id}")
        assert r.status_code == 200
        results = r.data.get("results", r.data)
        assert len(results) >= 1

    def test_quote_detail(self, api_client, seed_quotes):
        _, client = api_client
        _, _, quote = seed_quotes
        r = client.get(f"/api/quotes/{quote.id}/")
        assert r.status_code == 200
        assert r.data["supplier_name"] == "TestSup"
        assert len(r.data["items"]) >= 1

    def test_competitive_sheet(self, api_client, seed_quotes):
        _, client = api_client
        req, _, _ = seed_quotes
        r = client.get(
            "/api/quotes/competitive_sheet/",
            {"request_id": req.id},
        )
        assert r.status_code == 200
        assert r.data["total_quotes"] >= 1
        assert r.data["best"] is not None
        assert r.data["best"]["supplier_name"] == "TestSup"

    def test_competitive_sheet_missing_request(self, api_client, seed_quotes):
        _, client = api_client
        r = client.get("/api/quotes/competitive_sheet/")
        assert r.status_code == 400

    def test_create_quote(self, api_client, seed_quotes):
        _, client = api_client
        req, supplier, _ = seed_quotes
        r = client.post(
            "/api/quotes/",
            {
                "request": req.id,
                "supplier": supplier.id,
                "delivery_cost": 3000,
                "payment_terms": "30% prepay",
            },
        )
        assert r.status_code == 201
        assert r.data["payment_terms"] == "30% prepay"

    def test_unauthorized_cannot_access(self):
        client = APIClient()
        r = client.get("/api/quotes/")
        assert r.status_code == 401
