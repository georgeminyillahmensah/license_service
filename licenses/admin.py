from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import Brand, Product, LicenseKey, License, Activation


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    """Admin interface for Brand model."""
    
    list_display = ('name', 'slug', 'is_active', 'product_count', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'slug', 'description')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('name',)
    
    def product_count(self, obj):
        """Display count of products for this brand."""
        return obj.products.count()
    product_count.short_description = _('Products')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Admin interface for Product model."""
    
    list_display = ('name', 'brand', 'slug', 'is_active', 'license_count', 'created_at')
    list_filter = ('brand', 'is_active', 'created_at')
    search_fields = ('name', 'slug', 'description', 'brand__name')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('brand__name', 'name')
    
    def license_count(self, obj):
        """Display count of licenses for this product."""
        return obj.licenses.count()
    license_count.short_description = _('Licenses')


@admin.register(LicenseKey)
class LicenseKeyAdmin(admin.ModelAdmin):
    """Admin interface for LicenseKey model."""
    
    list_display = ('key_display', 'customer_email', 'brand', 'is_active', 'license_count', 'created_at')
    list_filter = ('brand', 'is_active', 'created_at')
    search_fields = ('key', 'customer_email', 'brand__name')
    readonly_fields = ('key', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    
    def key_display(self, obj):
        """Display truncated license key."""
        key_str = str(obj.key)
        return format_html('<code>{}</code>', key_str[:20] + '...')
    key_display.short_description = _('License Key')
    
    def license_count(self, obj):
        """Display count of licenses for this key."""
        return obj.licenses.count()
    license_count.short_description = _('Licenses')


@admin.register(License)
class LicenseAdmin(admin.ModelAdmin):
    """Admin interface for License model."""
    
    list_display = (
        'product', 'customer_email', 'license_key_display', 'status', 
        'seats', 'available_seats', 'expiration_date', 'is_expired_display'
    )
    list_filter = ('status', 'product__brand', 'product', 'expiration_date', 'created_at')
    search_fields = ('license_key__customer_email', 'product__name', 'product__brand__name')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        (None, {
            'fields': ('license_key', 'product', 'status', 'seats', 'expiration_date')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def customer_email(self, obj):
        """Display customer email from license key."""
        return obj.license_key.customer_email
    customer_email.short_description = _('Customer Email')
    
    def license_key_display(self, obj):
        """Display truncated license key."""
        key_str = str(obj.license_key.key)
        return format_html('<code>{}</code>', key_str[:15] + '...')
    license_key_display.short_description = _('License Key')
    
    def is_expired_display(self, obj):
        """Display expired status with color coding."""
        if obj.is_expired:
            return format_html('<span style="color: red;">{}</span>', _('Expired'))
        return format_html('<span style="color: green;">{}</span>', _('Active'))
    is_expired_display.short_description = _('Status')


@admin.register(Activation)
class ActivationAdmin(admin.ModelAdmin):
    """Admin interface for Activation model."""
    
    list_display = (
        'license_display', 'customer_email', 'instance_identifier', 
        'instance_type', 'is_active', 'activated_at'
    )
    list_filter = ('is_active', 'instance_type', 'license__product__brand', 'activated_at')
    search_fields = (
        'instance_identifier', 'license__product__name', 
        'license__license_key__customer_email'
    )
    readonly_fields = ('activated_at', 'deactivated_at', 'updated_at')
    ordering = ('-activated_at',)
    
    fieldsets = (
        (None, {
            'fields': ('license', 'instance_identifier', 'instance_type', 'is_active')
        }),
        (_('Timestamps'), {
            'fields': ('activated_at', 'deactivated_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def license_display(self, obj):
        """Display license information."""
        return f"{obj.license.product.name} ({obj.license.product.brand.name})"
    license_display.short_description = _('License')
    
    def customer_email(self, obj):
        """Display customer email from license."""
        return obj.license.license_key.customer_email
    customer_email.short_description = _('Customer Email')
