#!/usr/bin/env python3
"""Seed suppliers with real Russian construction material suppliers."""
import os, sys, django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from apps.suppliers.models import Supplier, SupplierAddress

SUPPLIERS = [
    ("Kerama Marazzi", "sales@kerama.ru", "+749***567", "Moscow", "Ostashkovskoe sh. 1", 55.8894, 37.6083),
    ("Unitile", "info@unitile.ru", "+749***678", "Podolsk", "Zheleznodorozhnaya 5", 55.4312, 37.5456),
    ("Estima Ceramica", "sale@estima.ru", "+749***789", "Moscow", "Nakhimovsky 24", 55.6685, 37.5712),
    ("Italon", "info@italon.ru", "+749***890", "Shcherbinka", "Kosmonavtov 10", 55.4997, 37.5597),
    ("CF Ceramica", "cf@ceramica.ru", "+749***901", "Khimki", "Leningradskoe 25", 55.8974, 37.4297),
    ("Granit Invest", "granit@invest.ru", "+734***567", "Ekaterinburg", "Malysheva 100", 56.8389, 60.6057),
    ("UralKeramika", "ural@keramika.ru", "+734***678", "Chelyabinsk", "Lenina 50", 55.1644, 61.4368),
    ("StroyKeramika", "info@stroykeram.ru", "+781***567", "SPb", "Moskovsky 150", 59.8910, 30.3180),
    ("KNAUF Gips", "knauf@knauf.ru", "+749***001", "Krasnogorsk", "Tsentralnaya 3", 55.8204, 37.3302),
    ("Weber Vetonit", "weber@vetonit.ru", "+749***002", "Moscow", "Ryazansky 32", 55.7263, 37.7662),
    ("Ceresit", "info@ceresit.ru", "+749***003", "Moscow", "Bolshaya Semenovskaya 40", 55.7822, 37.7122),
    ("Litokol", "litokol@litokol.ru", "+749***004", "Balashikha", "Entuziastov 50", 55.8042, 37.9567),
    ("TehnoNIKOL", "tehnonikol@tn.ru", "+749***005", "Moscow", "Gilyarovskogo 39", 55.7786, 37.6387),
    ("Rockwool", "russia@rockwool.ru", "+749***006", "Zheleznodorozhnyj", "Avtozavodskaya 25", 55.7390, 38.0162),
    ("Grand Line", "grandline@grandline.ru", "+781***001", "SPb", "Obukhovskoy 120", 59.8644, 30.4721),
    ("Petrovich", "info@petrovich.ru", "+781***100", "SPb", "Sofiyskaya 60", 59.8802, 30.4257),
    ("Petrovich", "msk@petrovich.ru", "+749***200", "Moscow", "Volgogradsky 42", 55.7145, 37.7523),
    ("Petrovich", "podolsk@petrovich.ru", "+749***201", "Podolsk", "Lenina 107", 55.4290, 37.5435),
    ("Lerua Merlen", "pro@leroymerlin.ru", "+749***010", "Moscow", "Borovskoe 2", 55.6521, 37.4139),
    ("Teplostroy", "info@teplostroy.ru", "+749***020", "Podolsk", "Yubileynaya 7", 55.4201, 37.5354),
]

count = 0
for name, email, phone, city, addr, lat, lon in SUPPLIERS:
    s, created = Supplier.objects.get_or_create(email=email, defaults={"name": name, "phone": phone})
    SupplierAddress.objects.get_or_create(supplier=s, address=addr, city=city,
        defaults={"latitude": lat, "longitude": lon})
    if created: count += 1

print(f"Seeded {count} new suppliers (total: {Supplier.objects.count()})")
print(f"Addresses: {SupplierAddress.objects.count()}")
