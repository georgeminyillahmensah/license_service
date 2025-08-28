from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from users.models import User
from django.utils import timezone
import uuid
import logging

logger = logging.getLogger(__name__)


class Brand(models.Model):
    """
    Represents a brand in the ecosystem (e.g., WP Rocket, RankMath, etc.)
    Each brand can have multiple products and manage their own licenses.
    """
    
    name = models.CharField(
        max_length=255, 
        unique=True,
        help_text=_("Brand name (e.g., WP Rocket, RankMath)")
    )
    
    slug = models.SlugField(
        max_length=100, 
        unique=True,
        help_text=_("URL-friendly brand identifier")
    )
    
    description = models.TextField(
        blank=True,
        help_text=_("Brand description")
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text=_("Whether this brand is active in the system")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'brands'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Product(models.Model):
    """
    Represents a product within a brand (e.g., RankMath Pro, Content AI addon)
    Each product can have multiple licenses associated with it.
    """
    
    name = models.CharField(
        max_length=255,
        help_text=_("Product name")
    )
    
    slug = models.SlugField(
        max_length=100,
        help_text=_("URL-friendly product identifier")
    )
    
    brand = models.ForeignKey(
        Brand,
        on_delete=models.CASCADE,
        related_name='products',
        help_text=_("Brand that owns this product")
    )
    
    description = models.TextField(
        blank=True,
        help_text=_("Product description")
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text=_("Whether this product is active")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'products'
        unique_together = ['brand', 'slug']
        ordering = ['brand__name', 'name']
    
    def __str__(self):
        return f"{self.brand.name} - {self.name}"


class LicenseKey(models.Model):
    """
    Represents a license key that can unlock multiple licenses.
    This is the main identifier that end users receive.
    """
    
    key = models.CharField(
        max_length=255, 
        unique=True,
        default=uuid.uuid4,
        help_text=_("Unique license key identifier")
    )
    
    customer_email = models.EmailField(
        help_text=_("Customer email address")
    )
    
    brand = models.ForeignKey(
        Brand,
        on_delete=models.CASCADE,
        related_name='license_keys',
        help_text=_("Brand that owns this license key")
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text=_("Whether this license key is active")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'license_keys'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['customer_email']),
            models.Index(fields=['brand']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        key_str = str(self.key)
        return f"{key_str[:8]}... ({self.customer_email})"
    
    def get_active_licenses(self):
        """Get all active licenses associated with this key."""
        return self.licenses.filter(status='valid')
    
    def get_total_seats(self):
        """Get total seats across all licenses."""
        return sum(license.seats for license in self.licenses.all())


class License(models.Model):
    """
    Represents a specific license for a product.
    Each license is associated with a license key and has its own lifecycle.
    """
    
    STATUS_CHOICES = [
        ('valid', _('Valid')),
        ('suspended', _('Suspended')),
        ('cancelled', _('Cancelled')),
        ('expired', _('Expired')),
        ('pending', _('Pending')),
        ('renewed', _('Renewed')),
    ]
    
    license_key = models.ForeignKey(
        LicenseKey,
        on_delete=models.CASCADE,
        related_name='licenses',
        help_text=_("License key this license belongs to")
    )
    
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='licenses',
        help_text=_("Product this license grants access to")
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='valid',
        help_text=_("Current status of the license")
    )
    
    seats = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        help_text=_("Number of seats/activations allowed")
    )
    
    expiration_date = models.DateTimeField(
        help_text=_("When this license expires")
    )
    
    # Lifecycle management fields
    original_expiration_date = models.DateTimeField(
        null=True, 
        blank=True,
        help_text=_("Original expiration date before renewal")
    )
    
    renewal_count = models.PositiveIntegerField(
        default=0,
        help_text=_("Number of times this license has been renewed")
    )
    
    suspension_reason = models.TextField(
        blank=True,
        help_text=_("Reason for suspension if applicable")
    )
    
    cancellation_reason = models.TextField(
        blank=True,
        help_text=_("Reason for cancellation if applicable")
    )
    
    cancelled_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text=_("When the license was cancelled")
    )
    
    suspended_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text=_("When the license was suspended")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'licenses'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['expiration_date']),
            models.Index(fields=['product']),
        ]
    
    def __str__(self):
        return f"{self.product.name} - {self.license_key.customer_email}"
    
    @property
    def is_expired(self):
        """Check if license has expired."""
        return timezone.now() > self.expiration_date
    
    @property
    def available_seats(self):
        """Calculate available seats."""
        used_seats = self.activations.filter(is_active=True).count()
        return max(0, self.seats - used_seats)
    
    def renew(self, new_expiration_date, reason=None):
        """Renew the license with a new expiration date."""
        
        if self.status not in ['valid', 'expired']:
            raise ValueError(f"Cannot renew license with status: {self.status}")
        
        # Store original expiration date if this is the first renewal
        if not self.original_expiration_date:
            self.original_expiration_date = self.expiration_date
        
        self.expiration_date = new_expiration_date
        self.renewal_count += 1
        self.status = 'renewed'
        self.save()
        
        # Log the renewal
        logger.info(
            f"License {self.id} renewed until {new_expiration_date} "
            f"(renewal #{self.renewal_count})"
        )
        
        return True
    
    def suspend(self, reason):
        """Suspend the license."""
        
        if self.status not in ['valid', 'renewed']:
            raise ValueError(f"Cannot suspend license with status: {self.status}")
        
        self.status = 'suspended'
        self.suspension_reason = reason
        self.suspended_at = timezone.now()
        self.save()
        
        # Log the suspension
        logger.info(f"License {self.id} suspended: {reason}")
        
        return True
    
    def resume(self):
        """Resume a suspended license."""
        if self.status != 'suspended':
            raise ValueError(f"Cannot resume license with status: {self.status}")
        
        self.status = 'valid'
        self.suspension_reason = ''
        self.suspended_at = None
        self.save()
        
        # Log the resumption
        logger.info(f"License {self.id} resumed")
        
        return True
    
    def cancel(self, reason):
        """Cancel the license."""
        
        if self.status in ['cancelled', 'expired']:
            raise ValueError(f"Cannot cancel license with status: {self.status}")
        
        self.status = 'cancelled'
        self.cancellation_reason = reason
        self.cancelled_at = timezone.now()
        self.save()
        
        # Log the cancellation
        logger.info(f"License {self.id} cancelled: {reason}")
        
        return True


class Activation(models.Model):
    """
    Represents an active license activation on a specific instance.
    Tracks seat usage and instance information.
    """
    
    license = models.ForeignKey(
        License,
        on_delete=models.CASCADE,
        related_name='activations',
        help_text=_("License being activated")
    )
    
    instance_identifier = models.CharField(
        max_length=500,
        help_text=_("Unique identifier for the instance (URL, hostname, machine ID)")
    )
    
    instance_type = models.CharField(
        max_length=100,
        blank=True,
        help_text=_("Type of instance (website, app, CLI, etc.)")
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text=_("Whether this activation is currently active")
    )
    
    activated_at = models.DateTimeField(auto_now_add=True)
    deactivated_at = models.DateTimeField(null=True, blank=True)
    deactivation_reason = models.TextField(
        blank=True,
        help_text=_("Reason for deactivation if applicable")
    )
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'activations'
        ordering = ['-activated_at']
        indexes = [
            models.Index(fields=['instance_identifier']),
            models.Index(fields=['is_active']),
            models.Index(fields=['license']),
        ]
        unique_together = ['license', 'instance_identifier']
    
    def __str__(self):
        return f"{self.license.product.name} on {self.instance_identifier}"
    
    def deactivate(self, reason=None):
        """Deactivate this activation."""
        self.is_active = False
        self.deactivated_at = timezone.now()
        self.deactivation_reason = reason or ''
        self.save()
        
        # Log the deactivation
        logger.info(
            f"Activation {self.id} deactivated for instance {self.instance_identifier}: "
            f"{reason or 'No reason provided'}"
        )
        
        return True
