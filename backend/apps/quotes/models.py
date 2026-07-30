from django.db import models
from apps.requests.models import Request, RequestItem
from apps.suppliers.models import Supplier

class RfqInvitation(models.Model):
    STATUS_CHOICES = [("pending","pending"),("sent","sent"),("replied","replied"),("no_response","no_response")]
    request = models.ForeignKey(Request, on_delete=models.CASCADE, related_name="invitations")
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    code = models.CharField(max_length=12)
    reply_code = models.CharField(max_length=16, unique=True, null=True, blank=True)
    reply_email = models.EmailField()
    quote_token = models.CharField(max_length=64, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    sent_at = models.DateTimeField(null=True, blank=True)
    replied_at = models.DateTimeField(null=True, blank=True)
    reminder_24h_sent_at = models.DateTimeField(null=True, blank=True)
    reminder_2h_sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = "rfq_invitations"

class EmailMessage(models.Model):
    D = [("inbound","inbound"),("outbound","outbound")]
    direction = models.CharField(max_length=10, choices=D)
    from_email = models.EmailField()
    to_email = models.EmailField()
    subject = models.TextField()
    body_text = models.TextField(blank=True)
    body_html = models.TextField(blank=True, default="")
    message_id = models.CharField(max_length=500, blank=True)
    request = models.ForeignKey(Request, on_delete=models.CASCADE, null=True, blank=True, related_name="emails")
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = "email_messages"

class Quote(models.Model):
    STATUS_CHOICES = [("received","received"),("valid","valid"),("selected","selected"),("rejected","rejected")]
    request = models.ForeignKey(Request, on_delete=models.CASCADE, related_name="quotes")
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    invitation = models.ForeignKey(RfqInvitation, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="received")
    delivery_cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    delivery_time = models.CharField(max_length=200, blank=True)
    payment_terms = models.CharField(max_length=500, blank=True)
    valid_until = models.DateField(null=True, blank=True)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = "quotes"
        ordering = ["-created_at"]

class QuoteItem(models.Model):
    quote = models.ForeignKey(Quote, on_delete=models.CASCADE, related_name="items")
    request_item = models.ForeignKey(RequestItem, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    vat_included = models.BooleanField(default=True)
    is_analog = models.BooleanField(default=False)
    brand = models.CharField(max_length=200, blank=True)
    confidence = models.FloatField(default=0.0)
    class Meta: db_table = "quote_items"

class CompetitiveSheet(models.Model):
    request = models.OneToOneField(Request, on_delete=models.CASCADE, related_name="competitive_sheet")
    best_supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)
    total_amount = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta: db_table = "competitive_sheets"
