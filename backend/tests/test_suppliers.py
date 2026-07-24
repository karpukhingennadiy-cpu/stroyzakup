import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from apps.requests.models import Category
from apps.suppliers.models import Supplier, SupplierAddress
from apps.requests.models import Address

User = get_user_model()


@pytest.fixture
def api_client():
    user = User.objects.create_user(
        email="sup@test.com", password="pass", username="sup@test.com"
    )
    client = APIClient()
    r = client.post("/api/auth/login/", {"email": "sup@test.com", "password": "pass"})
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {r.data["access"]}')
    return client


@pytest.fixture
def seed_suppliers():
    cat = Category.objects.get_or_create(slug="keram", defaults={"name": "Ceramics"})[0]
    s1 = Supplier.objects.create(name="StroyMir", email="s1@test.com", phone="+7999")
    SupplierAddress.objects.create(
        supplier=s1, address="Moscow", city="Moscow", latitude=55.75, longitude=37.62
    )
    s2 = Supplier.objects.create(name="Kerama", email="s2@test.com", phone="+7888")
    SupplierAddress.objects.create(
        supplier=s2, address="Podolsk", city="Podolsk", latitude=55.43, longitude=37.55
    )
    return s1, s2


@pytest.mark.django_db
class TestSuppliers:
    def test_list_suppliers(self, api_client, seed_suppliers):
        r = api_client.get("/api/suppliers/")
        assert r.status_code == 200
        results = r.data.get("results", r.data)
        assert len(results) >= 2

    def test_filter_by_city(self, api_client, seed_suppliers):
        r = api_client.get("/api/suppliers/?city=Moscow")
        assert r.status_code == 200
        results = r.data.get("results", r.data)
        names = [s["name"] for s in results]
        assert "StroyMir" in names

    def test_supplier_detail(self, api_client, seed_suppliers):
        s1, _ = seed_suppliers
        r = api_client.get(f"/api/suppliers/{s1.id}/")
        assert r.status_code == 200
        assert r.data["name"] == "StroyMir"
        assert len(r.data["addresses"]) >= 1

    def test_search_radius(self, api_client, seed_suppliers):
        r = api_client.get(
            "/api/suppliers/search_radius/",
            {"lat": 55.7, "lon": 37.6, "radius": 50},
        )
        assert r.status_code == 200
        assert len(r.data) >= 1

    def test_search_radius_far(self, api_client, seed_suppliers):
        r = api_client.get(
            "/api/suppliers/search_radius/",
            {"lat": 60.0, "lon": 30.0, "radius": 10},
        )
        assert r.status_code == 200
        assert len(r.data) == 0

    def test_create_supplier(self, api_client):
        r = api_client.post(
            "/api/suppliers/",
            {"name": "NewSup", "email": "new@test.com", "phone": "+7111"},
        )
        assert r.status_code == 201
        assert Supplier.objects.filter(name="NewSup").exists()

    def test_unauthorized_cannot_access(self):
        client = APIClient()
        r = client.get("/api/suppliers/")
        assert r.status_code == 401
