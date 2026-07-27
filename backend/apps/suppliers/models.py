from django.db import models

class Supplier(models.Model):
    name = models.CharField(max_length=500)
    legal_name = models.CharField(max_length=500, blank=True)
    inn = models.CharField(max_length=20, blank=True)
    site = models.URLField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField()
    is_active = models.BooleanField(default=True)
    supplier_type = models.CharField(max_length=20, default="unknown", choices=[("manufacturer","manufacturer"),("dealer","dealer"),("unknown","unknown")])
    source = models.CharField(max_length=20, default="seed", choices=[("seed","seed"),("llm","llm"),("web","web"),("2gis","2gis"),("manual","manual")])
    hidden_rating = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        db_table = "suppliers"
        ordering = ["name"]
    def __str__(self): return self.name

class SupplierAddress(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name="addresses")
    address = models.TextField()
    city = models.CharField(max_length=200)
    region = models.CharField(max_length=200, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    supplier_type = models.CharField(max_length=20, default="unknown", choices=[("manufacturer","manufacturer"),("dealer","dealer"),("unknown","unknown")])
    source = models.CharField(max_length=20, default="seed", choices=[("seed","seed"),("llm","llm"),("web","web"),("2gis","2gis"),("manual","manual")])
    class Meta: db_table = "supplier_addresses"

class SupplierCategory(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name="supplier_categories")
    category = models.ForeignKey("requests.Category", on_delete=models.CASCADE)
    is_main = models.BooleanField(default=False)
    class Meta: db_table = "supplier_categories"
