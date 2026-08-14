"""Admin extension: lightweight dashboard stats for superusers."""
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.db.models import Count


@staff_member_required
def dashboard_stats(request):
    from apps.requests.models import Request
    from apps.suppliers.models import Supplier
    from apps.quotes.models import Quote

    return JsonResponse({
        "requests": Request.objects.count(),
        "requests_by_status": dict(
            Request.objects.values_list("status").annotate(c=Count("id"))
        ),
        "suppliers": Supplier.objects.count(),
        "quotes": Quote.objects.count(),
        "quotes_received": Quote.objects.filter(status="received").count(),
    })
