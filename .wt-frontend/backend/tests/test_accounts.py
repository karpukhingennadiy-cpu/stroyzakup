import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()

@pytest.mark.django_db
class TestAuth:
    def test_register_user(self):
        client = APIClient()
        r = client.post('/api/auth/register/', {
            'email': 'test@example.com',
            'password': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User',
        })
        assert r.status_code == 201
        assert 'id' in r.data
        assert User.objects.filter(email='test@example.com').exists()

    def test_login_returns_tokens(self):
        User.objects.create_user(email='test@example.com', password='testpass123',
                                 username='test@example.com')
        client = APIClient()
        r = client.post('/api/auth/login/', {
            'email': 'test@example.com',
            'password': 'testpass123',
        })
        assert r.status_code == 200
        assert 'access' in r.data
        assert 'refresh' in r.data

    def test_me_requires_auth(self):
        client = APIClient()
        r = client.get('/api/auth/me/')
        assert r.status_code == 401

    def test_me_with_token(self):
        user = User.objects.create_user(email='me@test.com', password='pass',
                                         username='me@test.com')
        client = APIClient()
        login_r = client.post('/api/auth/login/', {'email': 'me@test.com', 'password': 'pass'})
        token = login_r.data['access']
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        r = client.get('/api/auth/me/')
        assert r.status_code == 200
        assert r.data['email'] == 'me@test.com'
