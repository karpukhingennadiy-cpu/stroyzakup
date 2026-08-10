# Email models: EmailMessage and RfqInvitation live in quotes app.
# This app provides views, services, and webhook handlers.
from django.db import models


class AiEmailLog(models.Model):
    # B9: audit log of every LLM draft generation (scenario, tokens, flags).
    # Used for debugging and eval of the email-writing pipeline.
    scenario = models.CharField(max_length=50, db_index=True)
    request_id = models.IntegerField(null=True, blank=True, db_index=True)
    prompt_preview = models.TextField(blank=True)
    response_preview = models.TextField(blank=True)
    needs_review = models.BooleanField(default=False, db_index=True)
    safety_reason = models.CharField(max_length=1000, blank=True)
    latency_ms = models.IntegerField(default=0)
    status = models.CharField(max_length=20, default="ok")
    source = models.CharField(max_length=20, default="llm")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ai_email_logs"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.scenario} #{self.request_id} review={self.needs_review}"
