from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """
    Custom User model for the license service.
    Extends Django's AbstractUser to add license-specific functionality.
    """
    
    # Additional fields for license management
    company_name = models.CharField(
        max_length=255, 
        blank=True, 
        null=True,
        help_text=_("Company or organization name")
    )
    
    phone_number = models.CharField(
        max_length=20, 
        blank=True, 
        null=True,
        help_text=_("Contact phone number")
    )
    
    address = models.TextField(
        blank=True, 
        null=True,
        help_text=_("Full address")
    )
    
    is_license_admin = models.BooleanField(
        default=False,
        help_text=_("Designates whether this user can manage licenses")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")
        db_table = 'users'
    
    def __str__(self):
        return f"{self.username} ({self.email})"
    
    def get_full_name_or_username(self):
        """Return full name if available, otherwise username."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
