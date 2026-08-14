from django.urls import path
from .models import dashboard_stats

urlpatterns = [
    path("stats/", dashboard_stats, name="admin-stats"),
]
