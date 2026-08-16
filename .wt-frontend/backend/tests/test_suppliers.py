import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from apps.suppliers.models import Supplier, SupplierAddress
from apps.requests.models import Category

User = get_user_model()

@pytest.fixture
def api_client():
    user = User.objects.create_user(email='sup@test.com', password='pass', username='sup@test.com')
    client = APIClient()
    r = client.post('/api/auth/login/', {'email': 'sup@test.com', 'password': 'pass'})
    token = r.data["access"]
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client

@pytest.fixture
def seed_suppliers():
    cat, _ = Category.objects.get_or_create(slug='keramogranit', defaults={'name': 'Keramogranit', 'default_radius_km': 150})
    suppliers = []
    data = [
        ('Kerama Marazzi', 'sales@kerama.ru', 'Moscow', 'ul. Tverskaya 1', 55.7558, 37.6173),
        ('Unitile', 'info@unitile.ru', 'Podolsk', 'ul. Kirova 5', 55.4312, 37.5456),
        ('Estima Ceramica', 'sales@estima.ru', 'Moscow', 'ul. Lenina 10', 55.7512, 37.6225),
        ('UralGranit', 'ural@granit.ru', 'Ekaterinburg', 'ul. Mira 50', 56.8389, 60.6057),
    ]
    for name, email, city, addr, lat, lon in data:
        s = Supplier.objects.create(name=name, email=email, phone='+79000000000')
        SupplierAddress.objects.create(supplier=s, address=addr, city=city, latitude=lat, longitude=lon)
        suppliers.append(s)
    return suppliers

@pytest.mark.django_db
class TestSuppliers:
    def test_list_suppliers(self, api_client, seed_suppliers):
        r = api_client.get('/api/suppliers/')
        assert r.status_code == 200
        assert r.data['count'] >= 4

    def test_filter_by_city(self, api_client, seed_suppliers):
        r = api_client.get('/api/suppliers/?city=Moscow')
        assert r.status_code == 200
        assert r.data['count'] >= 2

    def test_search_by_name(self, api_client, seed_suppliers):
        r = api_client.get('/api/suppliers/?search=Kerama')
        assert r.status_code == 200
        assert r.data['count'] == 1
        assert r.data['results'][0]['name'] == 'Kerama Marazzi'

    def test_supplier_detail(self, api_client, seed_suppliers):
        sid = seed_suppliers[0].id
        r = api_client.get(f'/api/suppliers/{sid}/')
        assert r.status_code == 200
        assert 'addresses' in r.data

    def test_radius_search(self, api_client, seed_suppliers):
        r = api_client.get('/api/suppliers/search_radius/?lat=55.75&lon=37.62&radius=50')
        assert r.status_code == 200
        moscow_nearby = [s for s in r.data if s['city'] == 'Moscow']
        assert len(moscow_nearby) >= 2

    def test_radius_excludes_far(self, api_client, seed_suppliers):
        r = api_client.get('/api/suppliers/search_radius/?lat=55.75&lon=37.62&radius=10')
        assert r.status_code == 200
        ekb = [s for s in r.data if s['city'] == 'Ekaterinburg']
        assert len(ekb) == 0

    def test_unauthorized(self):
        client = APIClient()
        r = client.get('/api/suppliers/')
        assert r.status_code == 401

    def test_create_supplier(self, api_client):
        r = api_client.post('/api/suppliers/', {
            'name': 'New Supplier', 'email': 'new@supplier.ru', 'phone': '+79998887766'
        })
        assert r.status_code == 201
        assert r.data['name'] == 'New Supplier'
