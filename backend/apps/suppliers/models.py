# backend/apps/suppliers/models.py
from django.db import models


class Supplier(models.Model):
    # FIX-H1: blank=True — DaData часто не возвращает email
    name = models.CharField(max_length=500, db_index=True)
    legal_name = models.CharField(max_length=500, blank=True, db_index=True)
    inn = models.CharField(max_length=20, blank=True, db_index=True)
    site = models.URLField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    moderation_status = models.CharField(
        max_length=20,
        choices=[
            ("unverified", "На проверке"),
            ("verified", "Подтверждён"),
            ("rejected", "Отклонён"),
        ],
        default="unverified",
        db_index=True,
    )
    source = models.CharField(
        max_length=20,
        choices=[
            ("seed", "Seed"),
            ("llm", "LLM"),
            ("web", "Web"),
            ("2gis", "2GIS"),
            ("dadata", "DaData"),
            ("manual", "Вручную"),
        ],
        default="manual",
        db_index=True,
    )
    supplier_type = models.CharField(
        max_length=20,
        default="unknown",
        choices=[
            ("manufacturer", "Производитель"),
            ("dealer", "Дилер"),
            ("unknown", "Неизвестно"),
        ],
        db_index=True,
    )
    hidden_rating = models.IntegerField(default=0)
    # Material sub-types this supplier handles (e.g. "резиновая плитка", "брусчатка")
    material_types = models.JSONField(default=list, blank=True)
    # Product catalog: description scraped from supplier website
    product_description = models.TextField(blank=True)
    # Product keywords: extracted product names/keywords from description
    product_keywords = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "suppliers"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["is_active", "moderation_status", "supplier_type"]),
        ]

    def __str__(self):
        return self.name


class SupplierAddress(models.Model):
    supplier = models.ForeignKey(
        Supplier, on_delete=models.CASCADE, related_name="addresses"
    )
    address = models.TextField()
    city = models.CharField(max_length=200, db_index=True)
    region = models.CharField(max_length=200, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "supplier_addresses"
        indexes = [
            models.Index(fields=["city", "is_active"]),
            models.Index(fields=["latitude", "longitude", "is_active"]),
        ]


class SupplierCategory(models.Model):
    supplier = models.ForeignKey(
        Supplier, on_delete=models.CASCADE, related_name="supplier_categories"
    )
    category = models.ForeignKey("requests.Category", on_delete=models.CASCADE)
    is_main = models.BooleanField(default=False)

    class Meta:
        db_table = "supplier_categories"
        unique_together = ("supplier", "category")  # FIX-H3
