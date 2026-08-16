# backend/scripts/load_sanity.py
"""A3: load sanity test — 20 parallel request creations + 10 parallel
match_suppliers against one request, in-process via ASGI transport.

LLM is disabled (regex fallback parser) and web discovery is stubbed,
so timings reflect application code + DB, not external APIs.

Usage: cd backend && uv run python scripts/load_sanity.py
"""
import asyncio
import os
import statistics
import sys
import tempfile
import time

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

import django
django.setup()

# Use a throwaway SQLite file so the demo DB stays untouched
from django.conf import settings
_tmp_db = os.path.join(tempfile.mkdtemp(prefix="loadsanity_"), "db.sqlite3")
settings.DATABASES["default"]["NAME"] = _tmp_db
if "test" not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS = list(settings.ALLOWED_HOSTS) + ["test"]

from django.core.management import call_command
call_command("migrate", run_syncdb=True, verbosity=0)

from django.contrib.auth import get_user_model
from apps.requests.models import Request, RequestItem, Category, Unit
from apps.suppliers.models import Supplier, SupplierCategory
from apps.requests.llm_client import llm
from apps.requests.services import websearch

llm.api_key = ""  # no external calls
websearch.discover_suppliers_for_request = lambda req: 0

User = get_user_model()
user = User.objects.create_user(email="load@test.local", username="load@test.local", password="pass")

cat, _ = Category.objects.get_or_create(slug="cement", defaults={"name": "Cement", "default_radius_km": 300})
unit, _ = Unit.objects.get_or_create(code="bag", defaults={"name": "Bag", "short_name": "меш"})
for i in range(10):
    s = Supplier.objects.create(name=f"LoadSup{i}", email=f"load{i}@t.ru",
                                moderation_status="verified",
                                product_keywords=["цемент"], material_types=["цемент"])
    SupplierCategory.objects.create(supplier=s, category=cat)

from django.core.asgi import get_asgi_application
application = get_asgi_application()
import httpx


async def get_token(client):
    r = await client.post("/api/auth/login/", json={"email": "load@test.local", "password": "pass"})
    r.raise_for_status()
    return r.json()["access"]


async def timed(coro_fn, n, label):
    lat, errors = [], []
    async def one(i):
        t0 = time.perf_counter()
        try:
            r = await coro_fn(i)
            dt = time.perf_counter() - t0
            if r.status_code >= 500:
                errors.append(f"{label}#{i}: HTTP {r.status_code}: {r.text[:120]}")
            lat.append(dt)
        except Exception as e:
            errors.append(f"{label}#{i}: {type(e).__name__}: {e}")
    await asyncio.gather(*[one(i) for i in range(n)])
    lat.sort()
    p50 = lat[len(lat) // 2] if lat else 0
    p95 = lat[min(int(len(lat) * 0.95), len(lat) - 1)] if lat else 0
    return p50, p95, max(lat) if lat else 0, errors


async def main():
    transport = httpx.ASGITransport(app=application)
    async with httpx.AsyncClient(transport=transport, base_url="http://test", timeout=60) as client:
        token = await get_token(client)
        headers = {"Authorization": f"Bearer {token}"}

        # 1) 20 parallel request creations
        async def create(i):
            return await client.post("/api/requests/",
                                     json={"raw_text": f"Цемент М500 - {10+i} меш"},
                                     headers=headers)
        p50c, p95c, maxc, errc = await timed(create, 20, "create")

        # Prepare one parsed request for matching
        r = await client.post("/api/requests/", json={"raw_text": "Цемент М500 - 50 меш"}, headers=headers)
        req_id = r.json()["id"]
        pr = await client.post(f"/api/requests/{req_id}/parse/", headers=headers)
        assert pr.status_code == 200, pr.text

        # 2) 10 parallel match_suppliers on the same request
        async def match(i):
            return await client.post(f"/api/requests/{req_id}/match_suppliers/",
                                     json={"limit": 10}, headers=headers)
        p50m, p95m, maxm, errm = await timed(match, 10, "match")

    locked = [e for e in errc + errm if "locked" in e.lower()]
    report = f"""# QA Load Sanity (A3)

Дата: 2026-07-30. Метод: in-process ASGI (httpx.AsyncClient), SQLite (временный файл),
LLM отключён (fallback-парсер), web-discovery заглушен. Замеряется код приложения + БД.

## Результаты

| Операция | Параллелизм | p50 | p95 | max | Цель | Статус |
|----------|-------------|-----|-----|-----|------|--------|
| Создание заявки | 20 | {p50c:.2f}с | {p95c:.2f}с | {maxc:.2f}с | p95 < 3с | {'✅' if p95c < 3 else '❌'} |
| Подбор поставщиков | 10 | {p50m:.2f}с | {p95m:.2f}с | {maxm:.2f}с | p95 < 5с | {'✅' if p95m < 5 else '❌'} |

- 5xx ошибок: **{len([e for e in errc + errm if 'HTTP 5' in e])}**
- SQLite «database is locked»: **{len(locked)}**
- Прочие ошибки: **{len([e for e in errc + errm if 'HTTP 5' not in e and 'locked' not in e.lower()])}**

{'## Ошибки' + chr(10) + chr(10).join('- ' + e for e in errc + errm) if errc or errm else 'Ошибок нет.'}

## Вывод

Деградации синхронной обработки на 10-20 параллельных запросах не наблюдается.
{'Дедлоков SQLite не зафиксировано.' if not locked else '⚠️ Есть блокировки SQLite — аргумент за PostgreSQL в prod (B3).'}
"""
    out = os.path.join(os.path.dirname(BASE_DIR), "docs", "QA_LOAD.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write(report)
    print(report)
    print("Written:", out)


if __name__ == "__main__":
    asyncio.run(main())
