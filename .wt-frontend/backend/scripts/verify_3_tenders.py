"""E2E verification of the 3 audit test tenders after fixes."""
import os, sys, django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
django.setup()

from apps.accounts.models import User
from apps.requests.models import Request, Address
from apps.requests.services.parser import parse_material_list
from apps.requests.services.matcher import match_suppliers

user = User.objects.first()
assert user, "No user in DB"

TENDERS = [
    ("Брусчатка 200х100х60 серая - 200 m2", "г. Подольск, ул. Парковая, 10", "Подольск", 55.4312, 37.5456),
    ("Резиновая плитка 600х600 - 150 m2", "г. Пенза, ул. Лермонтова, 5", "Пенза", 53.1950, 45.0180),
    ("Бетон М200 - 50 m3", "г. Иркутск, ул. Байкальская, 100", "Иркутск", 52.2860, 104.2810),
]

for raw, addr_text, city, lat, lon in TENDERS:
    addr = Address.objects.create(customer=user, address=addr_text, city=city, latitude=lat, longitude=lon)
    req = Request.objects.create(customer=user, code=f"VERIFY{Request.objects.count():03d}", raw_text=raw, address=addr)
    parse_material_list(req)
    items = list(req.items.all())
    matches = match_suppliers(req)
    print(f"\n### {raw} ({city})")
    for it in items:
        print(f"  item: {it.name} | cat={it.category.name if it.category else '-'} | mt={it.material_type or '-'}")
    print(f"  matches: {len(matches)}")
    for m in matches[:5]:
        print(f"    {m['total_score']:5.1f} | {m['name']:30s} | {m['supplier_type']:12s} | {m['city']} | {m['distance_km']} км")
    # cleanup
    req.delete(); addr.delete()
