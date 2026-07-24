from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = [("customer","Zakazchik"),("operator","Operator"),("admin","Admin")]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="customer")
    email = models.EmailField(unique=True)
    email_verified = models.BooleanField(default=False)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]
    class Meta:
        db_table = "users"

class CustomerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    company_name = models.CharField(max_length=500, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    inn = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = "customer_profiles"
