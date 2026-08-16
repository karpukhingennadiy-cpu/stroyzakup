import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from apps.requests.models import Request, RequestItem, Category, Unit
from apps.suppliers.models import Supplier
from apps.quotes.models import Quote, QuoteItem

User = get_user_model()

@pytest.fixture
def api_client():
    user = User.objects.create_user(email='qt@test.com', password='pass', username='qt@test.com')
    client = APIClient()
    r = client.post('/api/auth/login/', {'email': 'qt@test.com', 'password': 'pass'})
    token = r.data["access"]
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client

@pytest.fixture
def seed_data():
    cat, _ = Category.objects.get_or_create(slug='keramogranit', defaults={'name': 'Keramogranit', 'default_radius_km': 150})
    unit, _ = Unit.objects.get_or_create(code='m2', defaults={'name': 'Square meter', 'short_name': 'm2'})
    user = User.objects.get(email='qt@test.com')
    req = Request.objects.create(customer=user, code='TEST01', raw_text='Keramogranit 150m2', status='rfq_sent')
    item = RequestItem.objects.create(request=req, name='Keramogranit gray 600x600', category=cat, quantity=150, unit=unit, is_confirmed=True)
    sup1 = Supplier.objects.create(name='Best Ceramics', email='best@ceramics.ru')
    sup2 = Supplier.objects.create(name='Tile World', email='tile@world.ru')
    return {'req': req, 'item': item, 'sup1': sup1, 'sup2': sup2}

@pytest.mark.django_db
class TestQuotes:
    def test_create_quote(self, api_client, seed_data):
        r = api_client.post('/api/quotes/', {
            'request': seed_data['req'].id,
            'supplier': seed_data['sup1'].id,
            'delivery_cost': '5000',
            'payment_terms': 'Postoplata 50%',
            'delivery_time': '3-5 days',
        })
        assert r.status_code == 201
        assert r.data['supplier_name'] == 'Best Ceramics'

    def test_list_quotes_by_request(self, api_client, seed_data):
        Quote.objects.create(request=seed_data['req'], supplier=seed_data['sup1'])
        Quote.objects.create(request=seed_data['req'], supplier=seed_data['sup2'])
        r = api_client.get(f'/api/quotes/?request_id={seed_data["req"].id}')
        assert r.status_code == 200
        assert r.data['count'] == 2

    def test_competitive_sheet(self, api_client, seed_data):
        q1 = Quote.objects.create(request=seed_data['req'], supplier=seed_data['sup1'], delivery_cost=5000)
        QuoteItem.objects.create(quote=q1, request_item=seed_data['item'], price=850)
        q2 = Quote.objects.create(request=seed_data['req'], supplier=seed_data['sup2'], delivery_cost=3000)
        QuoteItem.objects.create(quote=q2, request_item=seed_data['item'], price=900)

        r = api_client.get(f'/api/quotes/competitive_sheet/?request_id={seed_data["req"].id}')
        assert r.status_code == 200
        assert len(r.data['suppliers']) == 2
        assert r.data['best'] is not None
        # Best should be sup1 (850*150+5000=132500 vs 900*150+3000=138000)
        assert r.data['best']['supplier_name'] == 'Best Ceramics'
