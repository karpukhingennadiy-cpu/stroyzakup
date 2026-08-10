# Email admin: EmailMessage and RfqInvitation are registered in quotes/admin.py.
# AiEmailLog is email-specific and registered here (B9).
from django.contrib import admin

from .models import AiEmailLog


@admin.register(AiEmailLog)
class AiEmailLogAdmin(admin.ModelAdmin):
    list_display = ("scenario", "request_id", "needs_review", "safety_reason", "latency_ms", "status", "created_at")
    list_filter = ("needs_review", "scenario", "status", "source")
    search_fields = ("request_id", "safety_reason", "prompt_preview", "response_preview")
    readonly_fields = ("scenario", "request_id", "prompt_preview", "response_preview",
                       "needs_review", "safety_reason", "latency_ms", "status", "source", "created_at")
    list_per_page = 50

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return True
