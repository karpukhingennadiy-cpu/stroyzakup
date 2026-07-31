# backend/tests/test_celery_mode.py
"""B2: USE_CELERY=True — views return 202 + task_id; sync fallback preserved.
Tasks run eagerly in tests (CELERY_TASK_ALWAYS_EAGER), no broker needed."""
import pytest
from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.test import APIClient

from apps.requests.models import Request, RequestItem, Category, Unit
from apps.requests.llm_client import llm
from apps.suppliers.models import Supplier

User = get_user_model()


@pytest.fixture
def api_client(db):
    User.objects.create_user(email="cel@test.com", password="pass", username="cel@test.com")
    client = APIClient()
    r = client.post("/api/auth/login/", {"email": "cel@test.com", "password": "pass"})
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {r.data['access']}")
    return client


@pytest.fixture(autouse=True)
def no_llm(monkeypatch):
    monkeypatch.setattr(llm, "api_key", "")


@pytest.mark.django_db
class TestCeleryMode:
    @override_settings(USE_CELERY=True)
    def test_parse_returns_202_with_task_id(self, api_client):
        r = api_client.post("/api/requests/", {"raw_text": "Цемент М500 - 10 меш"})
        req_id = r.data["id"]
        r = api_client.post(f"/api/requests/{req_id}/parse/")
        assert r.status_code == 202
        assert r.data["task_id"]
        assert r.data["status"] == "parsing"
        # Eager execution: task already ran synchronously under the hood
        req = Request.objects.get(id=req_id)
        assert req.status in ("parsed", "parsing")  # eager task finished or queued

    @override_settings(USE_CELERY=True)
    def test_match_returns_202_with_task_id(self, api_client):
        cat, _ = Category.objects.get_or_create(slug="cement", defaults={"name": "Cement"})
        r = api_client.post("/api/requests/", {"raw_text": "Цемент М500 - 10 меш"})
        req_id = r.data["id"]
        user = User.objects.get(email="cel@test.com")
        req = Request.objects.get(id=req_id)
        unit, _ = Unit.objects.get_or_create(code="bag", defaults={"name": "Bag", "short_name": "меш"})
        RequestItem.objects.create(request=req, raw_text="x", name="Цемент",
                                   category=cat, quantity=10, unit=unit, is_confirmed=True)
        req.status = "confirmed"
        req.save(update_fields=["status"])
        r = api_client.post(f"/api/requests/{req_id}/match_suppliers/", {"limit": 5}, format="json")
        assert r.status_code == 202
        assert r.data["task_id"]
        assert r.data["status"] == "matching"

    @override_settings(USE_CELERY=True)
    def test_send_rfq_returns_202_with_task_id(self, api_client):
        r = api_client.post("/api/requests/", {"raw_text": "Цемент М500 - 10 меш"})
        req_id = r.data["id"]
        Request.objects.filter(id=req_id).update(status="matched")
        sup = Supplier.objects.create(name="CelSup", email="cel@sup.ru")
        r = api_client.post(f"/api/requests/{req_id}/send_rfq/", {"supplier_ids": [sup.id]}, format="json")
        assert r.status_code == 202
        assert r.data["task_id"]

    @override_settings(USE_CELERY=False)
    def test_sync_fallback_preserved(self, api_client):
        r = api_client.post("/api/requests/", {"raw_text": "Цемент М500 - 10 меш"})
        req_id = r.data["id"]
        r = api_client.post(f"/api/requests/{req_id}/parse/")
        assert r.status_code == 200  # sync: immediate result, no task_id
        assert "task_id" not in r.data
        assert r.data["status"] == "confirmed"
