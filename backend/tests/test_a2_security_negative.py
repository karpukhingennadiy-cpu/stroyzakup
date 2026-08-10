# backend/tests/test_a2_security_negative.py
"""A2 (expanded): security-negative coverage - IDOR on actions, anonymous
access, nonexistent resources, param validation, staff permissions.

All LLM/geocoder calls are mocked - no real external API in tests.
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.requests.models import Request, RequestItem, Category, Unit
from apps.suppliers.models import Supplier, SupplierCategory
from apps.quotes.models import Quote, QuoteItem, RfqInvitation
from rest_framework.throttling import AnonRateThrottle

User = get_user_model()


def _login_client(email, password="pass", is_staff=False):
    User.objects.create_user(email=email, password=password, username=email,
                             is_staff=is_staff)
    client = APIClient()
    r = client.post("/api/auth/login/", {"email": email, "password": password})
    client.credentials(HTTP_AUTHORIZATION="Bearer " + r.data['access'])
    return client


@pytest.fixture
def owner(db):
    return _login_client("a2-owner@test.com")


@pytest.fixture
def other(db):
    return _login_client("a2-other@test.com")


@pytest.fixture
def staff(db):
    return _login_client("a2-staff@test.com", is_staff=True)


@pytest.fixture
def anon():
    return APIClient()


@pytest.fixture
def catalog(db):
    cat, _ = Category.objects.get_or_create(
        slug="cement", defaults={"name": "Cement", "default_radius_km": 300})
    Unit.objects.get_or_create(code="bag", defaults={"name": "Bag", "short_name": "меш"})
    return cat


@pytest.fixture
def owned_request(db, owner, catalog):
    """A request owned by  with one confirmed item and one matched supplier."""
    user = User.objects.get(email="a2-owner@test.com")
    req = Request.objects.create(customer=user, code="A2OWN1", raw_text="Cement M500 - 50 bag",
                                 status="confirmed")
    RequestItem.objects.create(request=req, raw_text="cement", name="Cement M500",
                               category=catalog, quantity=50, is_confirmed=True)
    sup = Supplier.objects.create(name="A2Sup", email="a2sup@t.ru",
                                  moderation_status="verified")
    SupplierCategory.objects.create(supplier=sup, category=catalog)
    return req


@pytest.fixture(autouse=True)
def no_external(monkeypatch):
    """Zero external calls: LLM disabled, websearch discovery no-op."""
    from apps.requests.llm_client import llm
    monkeypatch.setattr(llm, "api_key", "")
    from apps.requests.services import websearch
    monkeypatch.setattr(websearch, "discover_suppliers_for_request", lambda req: 0)


# --- IDOR: every request-scoped action must 404 for another user ------------

@pytest.mark.django_db
class TestActionIdor:
    def test_match_other_users_request_404(self, owner, other, owned_request):
        r = other.post(f"/api/requests/{owned_request.id}/match_suppliers/", format="json")
        assert r.status_code == 404

    def test_send_rfq_other_users_request_404(self, owner, other, owned_request):
        r = other.post(f"/api/requests/{owned_request.id}/send_rfq/",
                       {"supplier_ids": [1]}, format="json")
        assert r.status_code == 404

    def test_confirm_other_users_request_404(self, owner, other, owned_request):
        r = other.post(f"/api/requests/{owned_request.id}/confirm/", format="json")
        assert r.status_code == 404

    def test_items_other_users_request_404(self, owner, other, owned_request):
        r = other.get(f"/api/requests/{owned_request.id}/items/")
        assert r.status_code == 404

    def test_update_item_other_users_request_404(self, owner, other, owned_request):
        item = RequestItem.objects.get(request=owned_request)
        r = other.post(f"/api/requests/{owned_request.id}/update_item/",
                       {"item_id": item.id, "is_confirmed": True}, format="json")
        assert r.status_code == 404

    def test_complete_other_users_request_404(self, owner, other, owned_request):
        r = other.post(f"/api/requests/{owned_request.id}/complete/", format="json")
        assert r.status_code == 404


# --- Anonymous access: all authed endpoints must 401 ------------------------

@pytest.mark.django_db
class TestAnonymousAccess:
    def test_anon_parse_401(self, anon, owned_request):
        assert anon.post(f"/api/requests/{owned_request.id}/parse/").status_code == 401

    def test_anon_match_401(self, anon, owned_request):
        assert anon.post(f"/api/requests/{owned_request.id}/match_suppliers/",
                         format="json").status_code == 401

    def test_anon_send_rfq_401(self, anon, owned_request):
        assert anon.post(f"/api/requests/{owned_request.id}/send_rfq/",
                         {"supplier_ids": [1]}, format="json").status_code == 401

    def test_anon_confirm_401(self, anon, owned_request):
        assert anon.post(f"/api/requests/{owned_request.id}/confirm/",
                         format="json").status_code == 401

    def test_anon_complete_401(self, anon, owned_request):
        assert anon.post(f"/api/requests/{owned_request.id}/complete/",
                         format="json").status_code == 401

    def test_anon_items_401(self, anon, owned_request):
        assert anon.get(f"/api/requests/{owned_request.id}/items/").status_code == 401

    def test_anon_competitive_sheet_401(self, anon, owned_request):
        r = anon.get(f"/api/quotes/competitive_sheet/?request_id={owned_request.id}")
        assert r.status_code == 401

    def test_anon_quotes_list_401(self, anon):
        assert anon.get("/api/quotes/").status_code == 401

    def test_anon_suppliers_401(self, anon):
        assert anon.get("/api/suppliers/").status_code == 401

    def test_anon_geocode_401(self, anon):
        assert anon.post("/api/auth/geocode/", {"address": "Moscow"}).status_code == 401


# --- Nonexistent resources -> 404 --------------------------------------------

@pytest.mark.django_db
class TestNonexistentResource:
    def test_parse_missing_404(self, owner):
        assert owner.post("/api/requests/999999/parse/").status_code == 404

    def test_match_missing_404(self, owner):
        assert owner.post("/api/requests/999999/match_suppliers/", format="json").status_code == 404

    def test_send_rfq_missing_404(self, owner):
        assert owner.post("/api/requests/999999/send_rfq/",
                          {"supplier_ids": [1]}, format="json").status_code == 404

    def test_confirm_missing_404(self, owner):
        assert owner.post("/api/requests/999999/confirm/", format="json").status_code == 404

    def test_complete_missing_404(self, owner):
        assert owner.post("/api/requests/999999/complete/", format="json").status_code == 404

    def test_items_missing_404(self, owner):
        assert owner.get("/api/requests/999999/items/").status_code == 404

    def test_update_item_missing_item_404(self, owner, owned_request):
        r = owner.post(f"/api/requests/{owned_request.id}/update_item/",
                       {"item_id": 999999, "is_confirmed": True}, format="json")
        assert r.status_code == 404

    def test_quote_detail_missing_404(self, owner):
        assert owner.get("/api/quotes/999999/").status_code == 404


# --- search_radius parameter validation --------------------------------------

@pytest.mark.django_db
class TestRadiusValidation:
    def test_lat_alpha_400(self, owner):
        r = owner.get("/api/suppliers/search_radius/?lat=abc&lon=37.62&radius=50")
        assert r.status_code == 400

    def test_lon_alpha_400(self, owner):
        r = owner.get("/api/suppliers/search_radius/?lat=55.75&lon=xyz&radius=50")
        assert r.status_code == 400

    def test_radius_alpha_400(self, owner):
        r = owner.get("/api/suppliers/search_radius/?lat=55.75&lon=37.62&radius=big")
        assert r.status_code == 400

    def test_radius_missing_defaults_ok(self, owner):
        # defaults: lat=0, lon=0, radius=150 - must not 500
        r = owner.get("/api/suppliers/search_radius/")
        assert r.status_code == 200


# --- moderate / bulk_verify staff permissions --------------------------------

@pytest.mark.django_db
class TestModerationPermissions:
    def test_moderate_non_staff_403(self, owner, other, owned_request):
        from apps.suppliers.models import Supplier
        sup = Supplier.objects.create(name="ModSup", email="m@t.ru")
        r = owner.post(f"/api/suppliers/{sup.id}/moderate/", {"status": "verified"})
        assert r.status_code == 403

    def test_bulk_verify_non_staff_403(self, owner):
        r = owner.post("/api/suppliers/bulk_verify/", {"ids": [1]}, format="json")
        assert r.status_code == 403

    def test_moderate_invalid_status_400(self, staff):
        from apps.suppliers.models import Supplier
        sup = Supplier.objects.create(name="ModSup2", email="m2@t.ru")
        r = staff.post(f"/api/suppliers/{sup.id}/moderate/", {"status": "banana"})
        assert r.status_code == 400

    def test_bulk_verify_without_ids_400(self, staff):
        r = staff.post("/api/suppliers/bulk_verify/", {}, format="json")
        assert r.status_code == 400

    def test_bulk_verify_invalid_status_400(self, staff):
        r = staff.post("/api/suppliers/bulk_verify/",
                       {"ids": [1], "status": "banana"}, format="json")
        assert r.status_code == 400

    def test_moderate_staff_ok(self, staff):
        from apps.suppliers.models import Supplier
        sup = Supplier.objects.create(name="ModSup3", email="m3@t.ru")
        r = staff.post(f"/api/suppliers/{sup.id}/moderate/", {"status": "verified"})
        assert r.status_code == 200
        sup.refresh_from_db()
        assert sup.moderation_status == "verified"

    def test_bulk_verify_staff_ok(self, staff):
        from apps.suppliers.models import Supplier
        s1 = Supplier.objects.create(name="B1", email="b1@t.ru")
        s2 = Supplier.objects.create(name="B2", email="b2@t.ru")
        r = staff.post("/api/suppliers/bulk_verify/",
                       {"ids": [s1.id, s2.id], "status": "verified"}, format="json")
        assert r.status_code == 200
        assert r.data["updated"] == 2


# --- Quote create IDOR: must not attach a quote to someone else's request ----

@pytest.mark.django_db
class TestQuoteCreateIdor:
    def test_create_quote_other_users_request_rejected(self, owner, other, owned_request):
        """A customer must not be able to create a quote bound to another
        user's request (would corrupt their competitive sheet)."""
        sup = Supplier.objects.create(name="QSup", email="q@t.ru")
        r = other.post("/api/quotes/", {
            "request": owned_request.id,
            "supplier": sup.id,
            "delivery_cost": "100",
            "payment_terms": "predoplata",
            "delivery_time": "3 days",
        })
        assert r.status_code in (400, 404)

    def test_create_quote_own_request_ok(self, owner, owned_request):
        sup = Supplier.objects.create(name="QSup2", email="q2@t.ru")
        r = owner.post("/api/quotes/", {
            "request": owned_request.id,
            "supplier": sup.id,
            "delivery_cost": "100",
            "payment_terms": "predoplata",
            "delivery_time": "3 days",
        })
        assert r.status_code == 201


# --- Status guards and payload validation ------------------------------------

@pytest.mark.django_db
class TestStatusGuards:
    def test_send_rfq_from_draft_400(self, owner, owned_request):
        # owned_request is 'confirmed'; force back to draft
        Request.objects.filter(id=owned_request.id).update(status="draft")
        sup = Supplier.objects.create(name="SgSup", email="sg@t.ru")
        r = owner.post(f"/api/requests/{owned_request.id}/send_rfq/",
                       {"supplier_ids": [sup.id]}, format="json")
        assert r.status_code == 400

    def test_match_limit_alpha_400(self, owner, owned_request):
        r = owner.post(f"/api/requests/{owned_request.id}/match_suppliers/",
                       {"limit": "abc"}, format="json")
        assert r.status_code == 400

    def test_parse_from_confirmed_400(self, owner, owned_request):
        # already confirmed -> parse must be rejected
        r = owner.post(f"/api/requests/{owned_request.id}/parse/")
        assert r.status_code == 400


# --- Public quote: foreign request_item must be ignored silently -------------

@pytest.mark.django_db
class TestPublicQuoteForeignItem:
    def test_foreign_item_id_ignored(self, owner, other, owned_request, catalog):
        """Submitting a quote with a request_item belonging to another
        request must not attach it - quote is saved, item skipped."""
        from apps.emails.services import create_rfq_invitation
        user = User.objects.get(email="a2-owner@test.com")
        sup = Supplier.objects.create(name="PubSup", email="pub@t.ru")
        inv = create_rfq_invitation(owned_request, sup)

        # foreign item owned by a different request of 
        other_req = Request.objects.create(customer=User.objects.get(email="a2-other@test.com"),
                                           code="A2FOR1", raw_text="x")
        foreign_item = RequestItem.objects.create(request=other_req, raw_text="y",
                                                  name="Foreign item", category=catalog,
                                                  quantity=1, is_confirmed=True)
        own_item = RequestItem.objects.get(request=owned_request)

        client = APIClient()
        r = client.post(f"/api/public/quote/{inv.quote_token}/", {
            "items": [
                {"request_item_id": own_item.id, "price": 100},
                {"request_item_id": foreign_item.id, "price": 50},
            ]
        }, format="json")
        assert r.status_code == 200
        quote = Quote.objects.get(request=owned_request, supplier=sup)
        assert QuoteItem.objects.filter(quote=quote, request_item=foreign_item).count() == 0
        assert QuoteItem.objects.filter(quote=quote, request_item=own_item).count() == 1


# --- SEC-7: login brute-force throttle ---------------------------------------

@pytest.mark.django_db
class _LoginThrottleProbe(AnonRateThrottle):
    """Fixed-rate throttle for the login brute-force test. A class-level
     avoids DRF's frozen class attributes (api_settings is read once
    at import time, so override_settings has no effect once any request
    has been served)."""
    rate = "5/min"


@pytest.mark.django_db
class TestLoginThrottle:
    def test_login_throttled_after_30(self):
        from django.core.cache import cache
        from rest_framework_simplejwt.views import TokenObtainPairView
        cache.clear()
        old = TokenObtainPairView.throttle_classes
        TokenObtainPairView.throttle_classes = [_LoginThrottleProbe]
        try:
            client = APIClient()
            last = None
            for i in range(6):
                last = client.post("/api/auth/login/",
                                   {"email": "nobody@t.ru", "password": "wrong"})
            assert last.status_code == 429
        finally:
            TokenObtainPairView.throttle_classes = old
            cache.clear()


# --- Quote link deadline (+3 days) -------------------------------------------

@pytest.mark.django_db
class TestQuoteLinkDeadline:
    def test_expired_link_410(self, owner, owned_request):
        from datetime import timedelta
        from django.utils import timezone
        from apps.emails.services import create_rfq_invitation
        sup = Supplier.objects.create(name="ExpSup", email="exp@t.ru")
        inv = create_rfq_invitation(owned_request, sup)
        # Age the invitation past the 3-day window
        RfqInvitation.objects.filter(id=inv.id).update(
            created_at=timezone.now() - timedelta(days=4))
        client = APIClient()
        r = client.get(f"/api/public/quote/{inv.quote_token}/")
        assert r.status_code == 410

    def test_expired_link_post_410(self, owner, owned_request):
        from datetime import timedelta
        from django.utils import timezone
        from apps.emails.services import create_rfq_invitation
        sup = Supplier.objects.create(name="ExpSup2", email="exp2@t.ru")
        inv = create_rfq_invitation(owned_request, sup)
        RfqInvitation.objects.filter(id=inv.id).update(
            created_at=timezone.now() - timedelta(days=4))
        client = APIClient()
        r = client.post(f"/api/public/quote/{inv.quote_token}/",
                        {"items": [{"request_item_id": 1, "price": 100}]},
                        format="json")
        assert r.status_code == 410

    def test_fresh_link_ok(self, owner, owned_request):
        from apps.emails.services import create_rfq_invitation
        sup = Supplier.objects.create(name="FreshSup", email="fr@t.ru")
        inv = create_rfq_invitation(owned_request, sup)
        client = APIClient()
        r = client.get(f"/api/public/quote/{inv.quote_token}/")
        assert r.status_code == 200


# --- RequestCreateSerializer: address must not be writable (IDOR-lite) -------

@pytest.mark.django_db
class TestAddressIdorLite:
    def test_create_with_foreign_address_ignored(self, owner, other, catalog):
        """Passing another user's Address id in  must not attach it."""
        from apps.requests.models import Address
        owner_user = User.objects.get(email="a2-owner@test.com")
        other_user = User.objects.get(email="a2-other@test.com")
        foreign_addr = Address.objects.create(
            customer=other_user, address="Чужой адрес", city="Moscow",
            latitude=55.75, longitude=37.62)
        r = owner.post("/api/requests/", {
            "raw_text": "Цемент М500 - 50 меш",
            "address": foreign_addr.id,
        }, format="json")
        assert r.status_code == 201
        req = Request.objects.get(id=r.data["id"])
        assert req.address is None  # foreign address must NOT be attached
        assert req.raw_text == "Цемент М500 - 50 меш"

    def test_create_with_own_address_id_ignored(self, owner):
        """Even own Address id is ignored on create — use delivery_address."""
        from apps.requests.models import Address
        owner_user = User.objects.get(email="a2-owner@test.com")
        own_addr = Address.objects.create(
            customer=owner_user, address="Свой адрес", city="Moscow",
            latitude=55.75, longitude=37.62)
        r = owner.post("/api/requests/", {
            "raw_text": "Кирпич - 100 шт",
            "address": own_addr.id,
        }, format="json")
        assert r.status_code == 201
        req = Request.objects.get(id=r.data["id"])
        assert req.address is None

    def test_create_with_delivery_address_still_works(self, owner):
        """The supported path (delivery_address text) keeps working."""
        from apps.requests.models import Address
        r = owner.post("/api/requests/", {
            "raw_text": "Песок - 3 куб",
            "delivery_address": "Москва, Тверская 1",
            "latitude": 55.7558, "longitude": 37.6173,
            "city": "Москва",
        }, format="json")
        assert r.status_code == 201
        req = Request.objects.get(id=r.data["id"])
        assert req.address is not None
        assert req.address.customer.email == "a2-owner@test.com"
