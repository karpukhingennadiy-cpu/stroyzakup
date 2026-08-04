# backend/tests/test_metrics.py
"""G4: Prometheus /metrics endpoint smoke tests."""

import pytest
from django.test import Client


@pytest.mark.django_db
def test_metrics_endpoint_returns_200_and_prometheus_format():
    client = Client()
    # Generate some traffic so request counters are non-empty
    client.get("/api/health/")

    response = client.get("/metrics")

    assert response.status_code == 200
    assert "text/plain" in response["Content-Type"]
    body = response.content.decode()
    # django-prometheus exports these metric families
    assert "django_http_requests_total_by_view_transport_method" in body
    assert "django_http_requests_latency_seconds_by_view_method" in body


@pytest.mark.django_db
def test_metrics_counts_health_request():
    client = Client()
    client.get("/api/health/")

    body = client.get("/metrics").content.decode()

    # The health view must appear in the request counter series
    assert 'view="health"' in body
