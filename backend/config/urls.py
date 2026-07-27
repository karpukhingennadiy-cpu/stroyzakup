from django.contrib import admin
from django.urls import path, include
from apps.quotes.views import public_quote
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("apps.accounts.urls")),
    path("api/", include("apps.requests.urls")),
    path("api/", include("apps.suppliers.urls")),
    path("api/", include("apps.quotes.urls")),
    path("api/emails/", include("apps.emails.urls")),
    path("api/public/quote/<str:token>/", public_quote, name="public-quote"),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger"),
]
