from django.contrib import admin
from .models import Category, Unit, Request, RequestItem

@admin.register(Category)
class CatAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "default_radius_km", "is_active")

@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ("name", "short_name", "code")

@admin.register(Request)
class ReqAdmin(admin.ModelAdmin):
    list_display = ("code", "customer", "status", "created_at")
    list_filter = ("status",)

@admin.register(RequestItem)
class ItemAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "quantity", "confidence", "is_confirmed")
    list_filter = ("is_confirmed",)
