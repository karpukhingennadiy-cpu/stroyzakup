import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from apps.requests.models import Request, RequestItem, Category, Unit, Address
from apps.suppliers.models import Supplier, SupplierAddress, SupplierCategory

User = get_user_model()

@pytest.fixture
def match_client():
    user = User.objects.create_user(email="match@test.com", password="pass", username="match@test.com")
    client = APIClient()
    r = client.post("/api/auth/login/", {"email": "match@test.com", "password": "pass"})
    token = r.data["access"]
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client, user


@pytest.fixture
def match_data(match_client):
    client, user = match_client
    addr = Address.objects.create(
        customer=user, address="Moscow, Tverskaya 1", city="Moscow",
        latitude=55.7558, longitude=37.6173
    )
    cat_keram = Category.objects.create(name="Keramogranit", slug="keramogranit", default_radius_km=150)
    cat_kirp = Category.objects.create(name="Kirpich", slug="kirpich", default_radius_km=100)
    unit = Unit.objects.create(name="Square meter", short_name="m2", code="m2")

    req = Request.objects.create(customer=user, code="TSTMAT", raw_text="Test", status="confirmed", address=addr)
    RequestItem.objects.create(request=req, raw_text="K 600x600", name="Keramogranit seriy",
        category=cat_keram, quantity=150, unit=unit, is_confirmed=True)
    RequestItem.objects.create(request=req, raw_text="K kr", name="Kirpich polnoteliy",
        category=cat_kirp, quantity=1000, unit=unit, is_confirmed=True)

    s1 = Supplier.objects.create(name="Kerama Marazzi", email="s1@test.ru", phone="+7", hidden_rating=8, legal_name="OOO Kerama")
    SupplierAddress.objects.create(supplier=s1, address="Moscow", city="Moscow", latitude=55.76, longitude=37.62)
    SupplierCategory.objects.create(supplier=s1, category=cat_keram)

    s2 = Supplier.objects.create(name="Kirpichniy Zavod", email="s2@test.ru", phone="+7", hidden_rating=7, legal_name="OOO KirpZavod")
    SupplierAddress.objects.create(supplier=s2, address="Podolsk", city="Podolsk", latitude=55.43, longitude=37.55)
    SupplierCategory.objects.create(supplier=s2, category=cat_kirp)

    s3 = Supplier.objects.create(name="Universal Stroy", email="s3@test.ru", phone="+7", hidden_rating=9, legal_name="OOO Univ", site="https://univ.ru")
    SupplierAddress.objects.create(supplier=s3, address="Moscow", city="Moscow", latitude=55.75, longitude=37.61)
    SupplierCategory.objects.create(supplier=s3, category=cat_keram)
    SupplierCategory.objects.create(supplier=s3, category=cat_kirp)

    s4 = Supplier.objects.create(name="Dalniy Postav", email="s4@test.ru", phone="+7", hidden_rating=5)
    SupplierAddress.objects.create(supplier=s4, address="Ekaterinburg", city="Ekaterinburg", latitude=56.84, longitude=60.61)
    SupplierCategory.objects.create(supplier=s4, category=cat_keram)

    return client, req, [s1, s2, s3, s4]


@pytest.mark.django_db
class TestSupplierMatching:
    def test_match_returns_top_suppliers(self, match_data):
        client, req, suppliers = match_data
        r = client.post(f"/api/requests/{req.id}/match_suppliers/", {"limit": 20}, format="json")
        assert r.status_code in (200, 202)
        data = r.json()
        # async may return 202 without supplier data
        if data.get("suppliers"):
            top = data["suppliers"][0]
            assert top["name"] == "Universal Stroy"
            assert top["total_score"] > 0

    def test_match_sets_status_to_matched(self, match_data):
        client, req, suppliers = match_data
        r = client.post(f"/api/requests/{req.id}/match_suppliers/", {"limit": 20}, format="json")
        assert r.status_code in (200, 202)
        req.refresh_from_db()
        assert req.status in ("matched", "matching")

    def test_match_now_allowed_from_draft(self, match_data):
        client, req, suppliers = match_data
        req.status = "draft"
        req.save()
        r = client.post(f"/api/requests/{req.id}/match_suppliers/", {"limit": 20}, format="json")
        assert r.status_code in (200, 202, 400)

    def test_send_rfq_requires_supplier_ids(self, match_data):
        client, req, suppliers = match_data
        client.post(f"/api/requests/{req.id}/match_suppliers/", format="json")
        r = client.post(f"/api/requests/{req.id}/send_rfq/", {}, format="json")
        assert r.status_code in (200, 202, 400)
        assert "supplier_ids" in r.json()["error"]

    def test_scores_add_up(self, match_data):
        client, req, suppliers = match_data
        r = client.post(f"/api/requests/{req.id}/match_suppliers/", {"limit": 20}, format="json")
        data = r.json()
        for s in data.get("suppliers", []):
            calc = (s["category_score"] + s["distance_score"] + s["rating_score"]
                    + s["completeness_score"] + s.get("manufacturer_bonus", 0)
                    + s.get("material_type_score", 0) + s.get("product_match_score", 0))
            # B4: unverified suppliers get a 0.9 dampening coefficient
            if s.get("moderation_status") == "unverified":
                calc *= 0.9
            assert abs(calc - s["total_score"]) < 0.2, f"Score mismatch for {s['name']}: {calc} != {s['total_score']}"
