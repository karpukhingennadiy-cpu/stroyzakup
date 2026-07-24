"""
Seed suppliers with realistic data.
Run: cd backend && .venv/bin/python scripts/seed_suppliers.py
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

import django
django.setup()

from apps.suppliers.models import Supplier, SupplierAddress, SupplierCategory
from apps.requests.models import Category

SUPPLIERS = [
    {
        "name": "Petrovich",
        "legal_name": "OOO Petrovich",
        "inn": "7712345678",
        "site": "https://petrovich.ru",
        "phone": "+7495...567",
        "email": "sales@petrovich.ru",
        "addresses": [
            {"address": "g. Moscow, ul. Stroitelnaya, 15", "city": "Moscow", "region": "Moscow", "lat": 55.751, "lon": 37.618},
            {"address": "g. Podolsk, ul. Zheleznodorozhnaya, 5", "city": "Podolsk", "region": "Moscow Oblast", "lat": 55.431, "lon": 37.545},
        ],
        "categories": ["keramogranit", "plitochnyy_kley", "cement", "suhie_smesi"],
    },
    {
        "name": "Lerua Merlen",
        "legal_name": "OOO Lerua Merlen Vostok",
        "inn": "7723456789",
        "site": "https://leroymerlin.ru",
        "phone": "+7495...543",
        "email": "b2b@leroymerlin.ru",
        "addresses": [
            {"address": "g. Moscow, sh. Yaroslavskoe, 101", "city": "Moscow", "region": "Moscow", "lat": 55.85, "lon": 37.72},
        ],
        "categories": ["keramogranit", "kirpich", "bloki", "uteplitel", "krovlya"],
    },
    {
        "name": "TD Stroymaterialy",
        "legal_name": "OOO TD Stroymaterialy",
        "inn": "7834567890",
        "site": "https://tdstroy.ru",
        "phone": "+7812...212",
        "email": "info@tdstroy.ru",
        "addresses": [
            {"address": "g. SPb, ul. Sedova, 11", "city": "Saint Petersburg", "region": "Leningrad Oblast", "lat": 59.934, "lon": 30.335},
        ],
        "categories": ["cement", "nerudnye_materialy", "metalloprokat"],
    },
    {
        "name": "Kerama Marazzi",
        "legal_name": "OOO Kerama Marazzi",
        "inn": "5745678901",
        "site": "https://kerama-marazzi.com",
        "phone": "+7486...777",
        "email": "opt@kerama-marazzi.com",
        "addresses": [
            {"address": "g. Moscow, ul. Nametkina, 14", "city": "Moscow", "region": "Moscow", "lat": 55.657, "lon": 37.555},
        ],
        "categories": ["keramogranit", "plitochnyy_kley"],
    },
    {
        "name": "KNAUF Gips",
        "legal_name": "OOO KNAUF Gips",
        "inn": "5056789012",
        "site": "https://knauf.ru",
        "phone": "+7495...111",
        "email": "sales@knauf.ru",
        "addresses": [
            {"address": "g. Krasnogorsk, ul. Tsentralnaya, 2", "city": "Krasnogorsk", "region": "Moscow Oblast", "lat": 55.825, "lon": 37.335},
        ],
        "categories": ["suhie_smesi", "plitochnyy_kley", "uteplitel"],
    },
    {
        "name": "MetallProfil",
        "legal_name": "AO MetallProfil",
        "inn": "6678901234",
        "site": "https://metallprofil.ru",
        "phone": "+7343...500",
        "email": "sale@metallprofil.ru",
        "addresses": [
            {"address": "g. Ekaterinburg, ul. Metallurgov, 1", "city": "Ekaterinburg", "region": "Sverdlovsk Oblast", "lat": 56.838, "lon": 60.603},
        ],
        "categories": ["metalloprokat", "krovlya", "inzhenerka"],
    },
    {
        "name": "StroyDepo",
        "legal_name": "OOO StroyDepo",
        "inn": "2389012345",
        "site": "https://stroydepo.ru",
        "phone": "+7861...344",
        "email": "opt@stroydepo.ru",
        "addresses": [
            {"address": "g. Krasnodar, ul. Rossiyskaya, 100", "city": "Krasnodar", "region": "Krasnodar Krai", "lat": 45.035, "lon": 38.975},
        ],
        "categories": ["cement", "bloki", "kirpich"],
    },
    {
        "name": "Teplostroy",
        "legal_name": "OOO Teplostroy",
        "inn": "7701234567",
        "site": "",
        "phone": "+7495...321",
        "email": "teplo@stroy.ru",
        "addresses": [
            {"address": "g. Podolsk, ul. Pleshcheevskaya, 22", "city": "Podolsk", "region": "Moscow Oblast", "lat": 55.438, "lon": 37.553},
        ],
        "categories": ["uteplitel", "keramogranit"],
    },
]


def seed():
    for data in SUPPLIERS:
        s, created = Supplier.objects.get_or_create(
            email=data["email"],
            defaults={
                "name": data["name"],
                "legal_name": data["legal_name"],
                "inn": data["inn"],
                "site": data["site"],
                "phone": data["phone"],
            },
        )
        if created:
            for addr in data["addresses"]:
                SupplierAddress.objects.create(supplier=s, **addr)
            for cat_slug in data["categories"]:
                cat = Category.objects.filter(slug=cat_slug).first()
                if cat:
                    SupplierCategory.objects.get_or_create(supplier=s, category=cat)
        action = "Created" if created else "Exists"
        print(f"{action}: {s.name}")

    print(f"Total suppliers: {Supplier.objects.count()}")
    print(f"Total addresses: {SupplierAddress.objects.count()}")


if __name__ == "__main__":
    seed()
