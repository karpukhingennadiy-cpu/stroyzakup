# backend/tests/test_analytics.py
"""KC-03: PostHog analytics tests — service, signals, Celery tasks."""

import pytest
from unittest.mock import patch, MagicMock
from django.contrib.auth import get_user_model

from apps.analytics.services import AnalyticsService
from apps.analytics.tasks import track_event
from apps.requests.models import Request, RequestItem, Category, Unit
from apps.quotes.models import Quote, RfqInvitation
from apps.suppliers.models import Supplier

User = get_user_model()


class TestAnalyticsService:
    def test_hash_user_id_is_deterministic(self):
        svc = AnalyticsService()
        h1 = svc._hash_user_id(42)
        h2 = svc._hash_user_id(42)
        assert h1 == h2
        assert len(h1) == 32

    def test_hash_user_id_different_inputs(self):
        svc = AnalyticsService()
        assert svc._hash_user_id(1) != svc._hash_user_id(2)

    def test_capture_skips_when_disabled(self):
        svc = AnalyticsService()
        svc.enabled = False
        svc.client = None
        # Should not raise
        svc.capture(1, "test_event", {"foo": "bar"})

    def test_capture_raw_skips_when_disabled(self):
        svc = AnalyticsService()
        svc.enabled = False
        svc.client = None
        svc.capture_raw("distinct_id", "test_event", {"foo": "bar"})

    @patch("apps.analytics.services.Posthog")
    def test_capture_sends_with_lib_property(self, mock_posthog):
        mock_client = MagicMock()
        mock_posthog.return_value = mock_client
        svc = AnalyticsService()
        svc.client = mock_client
        svc.enabled = True
        svc.capture(42, "rfq_created", {"items_count": 3})
        mock_client.capture.assert_called_once()
        args, kwargs = mock_client.capture.call_args
        assert args[0] == svc._hash_user_id(42)
        assert args[1] == "rfq_created"
        assert args[2]["items_count"] == 3
        assert args[2]["$lib"] == "minitender-backend"

    @patch("apps.analytics.services.Posthog")
    def test_identify_strips_pii(self, mock_posthog):
        mock_client = MagicMock()
        mock_posthog.return_value = mock_client
        svc = AnalyticsService()
        svc.client = mock_client
        svc.enabled = True
        svc.identify(1, {"email": "a@b.com", "name": "Alice", "region": "Moscow"})
        args, kwargs = mock_client.identify.call_args
        props = args[1]
        assert "email" not in props
        assert "name" not in props
        assert props["region"] == "Moscow"


class TestTrackEventTask:
    @patch("apps.analytics.tasks.analytics")
    def test_track_event_calls_capture_raw(self, mock_analytics):
        track_event.run("rfq_created", "hashed_id", {"request_id": 1})
        mock_analytics.capture_raw.assert_called_once_with(
            "hashed_id", "rfq_created", {"request_id": 1}
        )

    @patch("apps.analytics.tasks.analytics")
    def test_track_event_retries_on_failure(self, mock_analytics):
        mock_analytics.capture_raw.side_effect = Exception("PostHog down")
        with pytest.raises(Exception):
            track_event.run("rfq_created", "hashed_id", {})


@pytest.mark.django_db
class TestAnalyticsSignals:
    @patch("apps.analytics.signals.track_event")
    def test_request_created_sends_rfq_created(self, mock_track):
        user = User.objects.create_user(email="sig@test.com", password="pass", username="sig@test.com")
        req = Request.objects.create(customer=user, code="SIG001")
        mock_track.delay.assert_called_once()
        args, kwargs = mock_track.delay.call_args
        assert kwargs["event"] == "rfq_created"
        assert kwargs["distinct_id"] is not None
        assert kwargs["properties"]["request_id"] == req.id

    @patch("apps.analytics.signals.track_event")
    def test_quote_received_sends_quote_received(self, mock_track):
        user = User.objects.create_user(email="qt@test.com", password="pass", username="qt@test.com")
        req = Request.objects.create(customer=user, code="QT001")
        sup = Supplier.objects.create(name="Sup", email="s@sup.ru")
        inv = RfqInvitation.objects.create(
            request=req, supplier=sup, code="INV001",
            reply_email="s@sup.ru", quote_token="token123"
        )
        Quote.objects.create(request=req, supplier=sup, invitation=inv)
        calls = [c for c in mock_track.delay.call_args_list if c.kwargs.get("event") == "quote_received"]
        assert len(calls) == 1

    @patch("apps.analytics.signals.track_event")
    def test_supplier_matched_sends_event(self, mock_track):
        user = User.objects.create_user(email="sm@test.com", password="pass", username="sm@test.com")
        req = Request.objects.create(customer=user, code="SM001", status="confirmed")
        cat = Category.objects.create(name="Cement", slug="cement")
        unit = Unit.objects.create(code="t", name="Tonne", short_name="т")
        RequestItem.objects.create(request=req, raw_text="x", name="Cement", category=cat, quantity=10, unit=unit)
        req.status = "matched"
        req.match_results = {"suppliers": [{"supplier_id": 1}], "count": 1}
        req.save(update_fields=["status", "match_results"])
        calls = [c for c in mock_track.delay.call_args_list if c.kwargs.get("event") == "supplier_matched"]
        assert len(calls) == 1
        props = calls[0].kwargs["properties"]
        assert props["suppliers_count"] == 1

    @patch("apps.analytics.signals.track_event")
    def test_winner_selected_sends_event(self, mock_track):
        user = User.objects.create_user(email="ws@test.com", password="pass", username="ws@test.com")
        req = Request.objects.create(customer=user, code="WS001")
        sup = Supplier.objects.create(name="Sup", email="s@sup.ru")
        inv = RfqInvitation.objects.create(
            request=req, supplier=sup, code="INV001",
            reply_email="s@sup.ru", quote_token="token456"
        )
        quote = Quote.objects.create(request=req, supplier=sup, invitation=inv, status="received")
        quote.status = "selected"
        quote.save(update_fields=["status"])
        calls = [c for c in mock_track.delay.call_args_list if c.kwargs.get("event") == "winner_selected"]
        assert len(calls) == 1
        assert calls[0].kwargs["properties"]["request_id"] == req.id
