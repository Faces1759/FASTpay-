from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ACCOUNT_TYPE_CHOICES = (
        ('personal', 'Personal'),
        ('business', 'Business'),
    )

    email = models.EmailField(unique=True)
    account_type = models.CharField(
        max_length=10,
        choices=ACCOUNT_TYPE_CHOICES,
        default='personal'
    )

    def __str__(self):
        return self.username


class Business(models.Model):
    BUSINESS_TYPE_CHOICES = (
        ('sole_proprietorship', 'Sole Proprietorship'),
        ('limited_liability', 'Limited Liability Company'),
        ('partnership', 'Partnership'),
        ('ngo', 'NGO/Non-Profit'),
        ('other', 'Other'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='business')
    company_name = models.CharField(max_length=200)
    rc_number = models.CharField(max_length=50, blank=True, help_text="CAC Registration Number")
    business_type = models.CharField(max_length=30, choices=BUSINESS_TYPE_CHOICES, default='sole_proprietorship')
    industry = models.CharField(max_length=100, blank=True)
    business_address = models.CharField(max_length=255, blank=True)
    tin_number = models.CharField(max_length=50, blank=True, help_text="Tax Identification Number")
    website = models.URLField(blank=True)
    verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.company_name