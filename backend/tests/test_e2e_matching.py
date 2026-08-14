import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from apps.requests.models import Request, RequestItem, Category, Unit, Address
from apps.suppliers.models import Supplier, SupplierAddress, SupplierCategory

User = get_user_model()

@pytest.mark.django_db
class TestE2EMatching:

    def test_full_flow(self, settings):
        settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
        client = APIClient()

        # 1. Register + login
        r = client.post("/api/auth/register/", {
            "email": "e2eflow@test.com", "password": "testpass123",
            "first_name": "E2E", "last_name": "Flow"
        })
        # Login to get token
        r = client.post("/api/auth/login/", {"email": "e2eflow@test.com", "password": "testpass123"})
        tok = r.json()["access"]
        client.credentials(HTTP_AUTHORIZATION="Bearer " + tok)
        user = User.objects.get(email="e2eflow@test.com")

        # 2. Address
        addr = Address.objects.create(customer=user, address="Moscow, Tverskaya 1",
            city="Moscow", latitude=55.7558, longitude=37.6173)

        # 3. Categories + units
        cat_keram, _ = Category.objects.get_or_create(slug="keram-e2e",
            defaults={"name": "Keramogranit", "default_radius_km": 150})
        cat_kirp, _ = Category.objects.get_or_create(slug="kirp-e2e",
            defaults={"name": "Kirpich", "default_radius_km": 100})
        unit, _ = Unit.objects.get_or_create(code="m2-e2e",
            defaults={"name": "Square meter", "short_name": "m2"})

        # 4. Suppliers with categories
        s1 = Supplier.objects.create(name="Kerama Marazzi", email="km@e2e.ru",
            phone="+7", hidden_rating=8, legal_name="OOO Kerama", site="https://kerama.ru")
        SupplierAddress.objects.create(supplier=s1, address="Moscow", city="Moscow",
            latitude=55.76, longitude=37.62)
        SupplierCategory.objects.create(supplier=s1, category=cat_keram)

        s2 = Supplier.objects.create(name="Kirpichniy Zavod", email="kz@e2e.ru",
            phone="+7", hidden_rating=6, legal_name="OOO KZ")
        SupplierAddress.objects.create(supplier=s2, address="Podolsk", city="Podolsk",
            latitude=55.43, longitude=37.55)
        SupplierCategory.objects.create(supplier=s2, category=cat_kirp)

        s3 = Supplier.objects.create(name="Universal Stroy", email="us@e2e.ru",
            phone="+7", hidden_rating=9, legal_name="OOO Univ", site="https://univ.ru")
        SupplierAddress.objects.create(supplier=s3, address="Moscow", city="Moscow",
            latitude=55.75, longitude=37.61)
        SupplierCategory.objects.create(supplier=s3, category=cat_keram)
        SupplierCategory.objects.create(supplier=s3, category=cat_kirp)

        s4 = Supplier.objects.create(name="Dalniy", email="dal@e2e.ru",
            phone="+7", hidden_rating=5)
        SupplierAddress.objects.create(supplier=s4, address="Ekaterinburg", city="Ekaterinburg",
            latitude=56.84, longitude=60.61)
        SupplierCategory.objects.create(supplier=s4, category=cat_keram)

        # 5. Create request
        r = client.post("/api/requests/", {"raw_text": "Keramogranit 600x600 - 150m2"}, format="json")
        assert r.status_code == 201
        req_id = r.json()["id"]

        # 6. Set address + items
        req = Request.objects.get(id=req_id)
        req.address = addr
        req.save()
        RequestItem.objects.create(request=req, raw_text="Keramogranit", name="Keramogranit seriy",
            category=cat_keram, quantity=150, unit=unit, is_confirmed=True)
        RequestItem.objects.create(request=req, raw_text="Kirpich", name="Kirpich polnoteliy",
            category=cat_kirp, quantity=1000, unit=unit, is_confirmed=True)

        # 7. Confirm
        r = client.post("/api/requests/{}/confirm/".format(req_id), format="json")
        assert r.status_code in (200, 202)
        status = r.json()["status"]
        assert status in ("confirmed", "matched", "matching"), f"Expected confirmed/matched, got {status}"

        # 8. GET MATCH RESULTS (eager mode returns suppliers synchronously)
        if status == "matched":
            # Confirm auto-matched - get results from confirm response
            data = r.json()
        else:
            r = client.post("/api/requests/{}/match_suppliers/".format(req_id), {"limit": 20}, format="json")
            data = r.json()
        assert r.status_code in (200, 202)
        suppliers = data.get("suppliers") or []
        assert data.get("status") == "matched", "Eager mode must finish matching synchronously"
        assert len(suppliers) > 0, "Eager mode must return matched suppliers"

        # 9. Verify Universal Stroy is #1
        top = suppliers[0]
        assert top["name"] == "Universal Stroy", "Got: {}".format(top["name"])
        assert top.get("matched_count", 0) == 2
        assert top.get("total_score", 0) > 85

        # 10. Status -> matched
        req.refresh_from_db()
        assert req.status in ("matched", "matching")

        # 11. Scores add up
        for s in suppliers:
            calc = (s.get("category_score", 0) + s.get("distance_score", 0)
                    + s.get("rating_score", 0) + s.get("completeness_score", 0)
                    + s.get("manufacturer_bonus", 0)
                    + s.get("material_type_score", 0) + s.get("product_match_score", 0))
            if s.get("moderation_status") == "unverified":
                calc *= 0.9
            assert abs(calc - s.get("total_score", 0)) < 0.2

        # 12. send_rfq without supplier_ids = 400
        r = client.post("/api/requests/{}/send_rfq/".format(req_id), {}, format="json")
        assert r.status_code == 400
        assert "supplier_ids" in r.json()["error"]

        # 13. send_rfq with supplier_ids from matched suppliers
        supplier_ids = [s["supplier_id"] for s in suppliers]
        assert supplier_ids, "Matched suppliers must provide supplier_ids"
        r = client.post("/api/requests/{}/send_rfq/".format(req_id),
            {"supplier_ids": supplier_ids}, format="json")
        assert r.status_code in (200, 202)