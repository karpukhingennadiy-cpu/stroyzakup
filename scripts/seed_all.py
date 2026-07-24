#!/usr/bin/env python3
"""Seed categories and units for StroyZakup"""
import os, sys, django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from apps.requests.models import Category, Unit

cats = [
    ("Керамогранит и плитка","keramogranit",150),
    ("Плиточный клей","plitochnyj_klej",100),
    ("Цемент","cement",150),
    ("Сухие смеси","suhie_smesi",150),
    ("Кирпич","kirpich",150),
    ("Блоки","bloki",150),
    ("Металлопрокат","metalloprokat",300),
    ("Пиломатериалы","pilomaterialy",200),
    ("Нерудные материалы","nerudnye",100),
    ("Утеплитель","uteplitel",200),
    ("Кровля","krovlya",200),
    ("Инженерные системы","inzhenerka",300),
    ("Лакокрасочные","lakokraska",200),
    ("Гипсокартон","gipsokarton",150),
    ("Другое","drugoe",300),
]
for name, slug, r in cats:
    c, created = Category.objects.get_or_create(slug=slug, defaults={"name":name,"default_radius_km":r})
    print(f"{'NEW' if created else 'OK'}: {name}")

units = [
    ("Квадратный метр","м2","m2"),
    ("Кубический метр","м3","m3"),
    ("Килограмм","кг","kg"),
    ("Тонна","т","ton"),
    ("Мешок","меш","bag"),
    ("Штука","шт","piece"),
    ("Упаковка","уп","pack"),
    ("Рулон","рул","roll"),
    ("Погонный метр","пог.м","linear_meter"),
    ("Литр","л","liter"),
    ("Комплект","компл","set"),
    ("Лист","лист","sheet"),
]
for name, short, code in units:
    u, created = Unit.objects.get_or_create(code=code, defaults={"name":name,"short_name":short})
    print(f"{'NEW' if created else 'OK'}: {name}")

print(f"Done: {Category.objects.count()} cats, {Unit.objects.count()} units")
