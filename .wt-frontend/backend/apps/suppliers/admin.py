from django.contrib import admin
from .models import Supplier, SupplierAddress

@admin.register(Supplier)
class SupAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "phone", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "email")

@admin.register(SupplierAddress)
class AddrAdmin(admin.ModelAdmin):
    list_display = ("supplier", "city", "address")
