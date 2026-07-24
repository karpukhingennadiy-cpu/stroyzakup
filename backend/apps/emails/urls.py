from django.urls import path

from . import views

urlpatterns = [
    path("webhook/mailgun/", views.mailgun_inbound_webhook, name="mailgun-webhook"),
    path("webhook/inbound/", views.generic_inbound_webhook, name="generic-inbound-webhook"),
]
