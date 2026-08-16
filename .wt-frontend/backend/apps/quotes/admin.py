from django.contrib import admin
from .models import RfqInvitation, EmailMessage, Quote, QuoteItem, CompetitiveSheet

@admin.register(RfqInvitation)
class RfqAd(admin.ModelAdmin): list_display = ("code", "supplier", "status", "sent_at")

@admin.register(EmailMessage)
class EmAd(admin.ModelAdmin): list_display = ("direction", "from_email", "subject"); list_filter = ("direction",)

@admin.register(Quote)
class QtAd(admin.ModelAdmin): list_display = ("supplier", "request", "status", "delivery_cost")

@admin.register(CompetitiveSheet)
class CsAd(admin.ModelAdmin): list_display = ("request", "best_supplier", "total_amount")
