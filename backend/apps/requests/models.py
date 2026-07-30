from django.db import models
from apps.accounts.models import User

class Category(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    default_radius_km = models.IntegerField(default=150)
    is_active = models.BooleanField(default=True)
    class Meta: db_table = "categories"
    def __str__(self): return self.name

class Unit(models.Model):
    name = models.CharField(max_length=100)
    short_name = models.CharField(max_length=20)
    code = models.CharField(max_length=30, unique=True)
    class Meta: db_table = "units"
    def __str__(self): return self.short_name

class Address(models.Model):
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="addresses")
    address = models.TextField()
    city = models.CharField(max_length=200)
    region = models.CharField(max_length=200, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = "addresses"

class Request(models.Model):
    STATUS_CHOICES = [
        ("draft","draft"),("parsing","parsing"),("confirmed","confirmed"),
        ("matching","matching"),("matched","matched"),("rfq_sent","rfq_sent"),
        ("rfq_failed","rfq_failed"),("collecting_quotes","collecting_quotes"),
        ("ready","ready"),("completed","completed"),("cancelled","cancelled"),
    ]
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="requests")
    code = models.CharField(max_length=12, unique=True, db_index=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="draft")
    address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True, blank=True)
    raw_text = models.TextField(blank=True)
    source = models.CharField(max_length=20, default="web")
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        db_table = "requests"
        ordering = ["-created_at"]
    def __str__(self): return f"RFQ-{self.code}"

class MaterialProfile(models.Model):
    """LLM-analyzed material knowledge: what the material is, its synonyms,
    and who typically produces/supplies it. Cached per normalized query."""
    query = models.CharField(max_length=300, unique=True, db_index=True)
    canonical_name = models.CharField(max_length=300, blank=True)
    material_type = models.CharField(max_length=200, blank=True, db_index=True)
    category_hint = models.CharField(max_length=100, blank=True)
    synonyms = models.JSONField(default=list, blank=True)
    search_queries = models.JSONField(default=list, blank=True)
    supplier_hints = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = "material_profiles"
    def __str__(self): return f"{self.query} → {self.canonical_name}"

class RequestItem(models.Model):
    request = models.ForeignKey(Request, on_delete=models.CASCADE, related_name="items")
    raw_text = models.TextField()
    name = models.CharField(max_length=500)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    unit = models.ForeignKey(Unit, on_delete=models.SET_NULL, null=True)
    brand = models.CharField(max_length=200, blank=True)
    spec = models.TextField(blank=True)
    material_type = models.CharField(max_length=200, blank=True, db_index=True)
    confidence = models.FloatField(default=0.0)
    is_confirmed = models.BooleanField(default=False)
    class Meta: db_table = "request_items"
