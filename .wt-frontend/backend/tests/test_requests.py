import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from apps.requests.models import Category, Unit

User = get_user_model()

@pytest.fixture
def api_client():
    user = User.objects.create_user(email='req@test.com', password='pass', username='req@test.com')
    client = APIClient()
    r = client.post('/api/auth/login/', {'email': 'req@test.com', 'password': 'pass'})
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {r.data['access']}")
    return client

@pytest.fixture
def seed_data():
    Category.objects.get_or_create(slug='test_cat', defaults={'name': 'TestCat', 'default_radius_km': 100})
    Unit.objects.get_or_create(code='m2', defaults={'name': 'Square meter', 'short_name': 'm2'})

@pytest.mark.django_db
class TestRequests:
    def test_create_request(self, api_client):
        r = api_client.post('/api/requests/', {'raw_text': 'Test material 100 m2', 'comment': 'test'})
        assert r.status_code == 201
        assert r.data['status'] == 'draft'
        assert len(r.data['code']) == 6

    def test_list_requests(self, api_client):
        api_client.post('/api/requests/', {'raw_text': 'Item 1'})
        api_client.post('/api/requests/', {'raw_text': 'Item 2'})
        r = api_client.get('/api/requests/')
        assert r.status_code == 200
        assert len(r.data.get('results', r.data)) >= 2

    def test_get_request_detail(self, api_client):
        create_r = api_client.post('/api/requests/', {'raw_text': 'Detail test'})
        req_id = create_r.data['id']
        r = api_client.get(f'/api/requests/{req_id}/')
        assert r.status_code == 200
        assert r.data['code']

    def test_unauthorized_cannot_access(self):
        client = APIClient()
        r = client.get('/api/requests/')
        assert r.status_code == 401
