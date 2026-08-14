# backend/config/urls.py
from django.contrib import admin
from django.http import JsonResponse
from django.urls import path, include
from apps.quotes.views import public_quote
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView


def health(request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health, name="health"),
    path("api/auth/", include("apps.accounts.urls")),
    path("api/", include("apps.requests.urls")),
    path("api/", include("apps.suppliers.urls")),
    path("api/", include("apps.quotes.urls")),
    path("api/emails/", include("apps.emails.urls")),
    path("api/assistant/", include("apps.assistant.urls")),
    path("admin-ext/", include("apps.admin_ext.urls")),
    # FIX-K3: убран двойной слеш, добавлен параметр token
    path("api/public/quote/<str:token>/", public_quote, name="public-quote"),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger"),
]