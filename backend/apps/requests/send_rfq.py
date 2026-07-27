import os
"""Send RFQ emails to matched suppliers."""
from django.core.mail import EmailMultiAlternatives
from apps.emails.services import create_rfq_invitation, build_rfq_email
from apps.suppliers.models import Supplier
from apps.quotes.models import EmailMessage

def send_rfq_to_suppliers(request_obj, supplier_ids):
    """Send RFQ to selected suppliers. Requires explicit supplier_ids list."""
    suppliers = Supplier.objects.filter(id__in=supplier_ids)
    results = []
    for supplier in suppliers:
        inv = create_rfq_invitation(request_obj, supplier)
        email_data = build_rfq_email(inv)
        msg = EmailMultiAlternatives(
            subject=email_data["subject"], body=email_data["body_text"],
            from_email=os.environ.get("FROM_EMAIL", "Минитендер RFQ <rfq@minitender.ru>"),
            to=[supplier.email], reply_to=[inv.reply_email])
        if email_data.get("body_html"):
            msg.attach_alternative(email_data["body_html"], "text/html")
        try:
            msg.send(fail_silently=False)
            EmailMessage.objects.create(
                direction="outbound", from_email="rfq@minitender.ru",
                to_email=supplier.email, subject=email_data["subject"],
                body_text=email_data["body_text"], request=request_obj, supplier=supplier)
            inv.status = "sent"
            results.append({"supplier": supplier.name, "status": "sent", "reply_to": inv.reply_email})
        except Exception as e:
            results.append({"supplier": supplier.name, "status": "error", "error": str(e)})
        inv.save()
    request_obj.status = "rfq_sent"
    request_obj.save(update_fields=["status"])
    return results
