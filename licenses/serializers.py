from rest_framework import serializers
from .models import Brand, Product, LicenseKey, License, Activation
from django.utils import timezone


class BrandSerializer(serializers.ModelSerializer):
    """Serializer for Brand model."""
    
    product_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Brand
        fields = ['id', 'name', 'slug', 'description', 'is_active', 'product_count', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def get_product_count(self, obj):
        return obj.products.count()


class ProductSerializer(serializers.ModelSerializer):
    """Serializer for Product model."""
    
    brand = BrandSerializer(read_only=True)
    brand_id = serializers.IntegerField(write_only=True)
    license_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = ['id', 'name', 'slug', 'brand', 'brand_id', 'description', 'is_active', 'license_count', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def get_license_count(self, obj):
        return obj.licenses.count()


class LicenseKeySerializer(serializers.ModelSerializer):
    """Serializer for LicenseKey model."""
    
    brand = BrandSerializer(read_only=True)
    brand_id = serializers.IntegerField(write_only=True)
    license_count = serializers.SerializerMethodField()
    
    class Meta:
        model = LicenseKey
        fields = ['id', 'key', 'customer_email', 'brand', 'brand_id', 'is_active', 'license_count', 'created_at']
        read_only_fields = ['id', 'key', 'created_at']
    
    def get_license_count(self, obj):
        return obj.licenses.count()


class LicenseSerializer(serializers.ModelSerializer):
    """Serializer for License model."""
    
    license_key = LicenseKeySerializer(read_only=True)
    license_key_id = serializers.IntegerField(write_only=True)
    product = ProductSerializer(read_only=True)
    product_id = serializers.IntegerField(write_only=True)
    available_seats = serializers.ReadOnlyField()
    is_expired = serializers.ReadOnlyField()
    
    # Lifecycle management fields
    original_expiration_date = serializers.ReadOnlyField()
    renewal_count = serializers.ReadOnlyField()
    suspension_reason = serializers.ReadOnlyField()
    cancellation_reason = serializers.ReadOnlyField()
    cancelled_at = serializers.ReadOnlyField()
    suspended_at = serializers.ReadOnlyField()
    
    class Meta:
        model = License
        fields = [
                    'id', 'license_key', 'license_key_id', 'product', 'product_id',
        'status', 'seats', 'available_seats', 'expiration_date', 
        'is_expired', 'original_expiration_date', 'renewal_count',
        'suspension_reason', 'cancellation_reason', 'cancelled_at',
        'suspended_at', 'created_at'
        ]
        read_only_fields = ['id', 'available_seats', 'is_expired', 'created_at']
    
    def validate(self, data):
        """Validate license data."""
        # Check if expiration date is in the future
        if 'expiration_date' in data and data['expiration_date'] <= timezone.now():
            raise serializers.ValidationError("Expiration date must be in the future.")
        
        # Check if seats is positive
        if 'seats' in data and data['seats'] <= 0:
            raise serializers.ValidationError("Seats must be a positive number.")
        
        return data


class ActivationSerializer(serializers.ModelSerializer):
    """Serializer for Activation model."""
    
    license = LicenseSerializer(read_only=True)
    license_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = Activation
        fields = [
                    'id', 'license', 'license_id', 'instance_identifier', 
        'instance_type', 'is_active', 'activated_at', 'deactivated_at',
        'deactivation_reason'
        ]
        read_only_fields = ['id', 'activated_at', 'deactivated_at']
    
    def validate(self, data):
        """Validate activation data."""
        license_obj = data.get('license_id')
        instance_identifier = data.get('instance_identifier')
        
        if license_obj and instance_identifier:
            # Check if activation already exists for this license and instance
            existing_activation = Activation.objects.filter(
                license_id=license_obj,
                instance_identifier=instance_identifier,
                is_active=True
            ).first()
            
            if existing_activation:
                raise serializers.ValidationError(
                    "An active activation already exists for this license and instance."
                )
        
        return data


class LicenseKeyDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for LicenseKey with all related licenses."""
    
    brand = BrandSerializer(read_only=True)
    licenses = LicenseSerializer(many=True, read_only=True)
    total_seats = serializers.SerializerMethodField()
    active_seats = serializers.SerializerMethodField()
    
    class Meta:
        model = LicenseKey
        fields = [
            'id', 'key', 'customer_email', 'brand', 'licenses', 
            'total_seats', 'active_seats', 'is_active', 'created_at'
        ]
    
    def get_total_seats(self, obj):
        return obj.get_total_seats()
    
    def get_active_seats(self, obj):
        return sum(license.available_seats for license in obj.licenses.all())


class LicenseStatusSerializer(serializers.Serializer):
    """Serializer for license status checks."""
    
    license_key = serializers.CharField(max_length=255)
    product_slug = serializers.CharField(max_length=100, required=False)
    instance_identifier = serializers.CharField(max_length=500, required=False)
    
    def validate_license_key(self, value):
        """Validate license key format."""
        if not value or len(value) < 10:
            raise serializers.ValidationError("Invalid license key format.")
        return value


class LicenseRenewalSerializer(serializers.Serializer):
    """Serializer for license renewal requests."""
    
    new_expiration_date = serializers.DateTimeField(
        help_text="New expiration date for the license"
    )
    reason = serializers.CharField(
        max_length=500,
        required=False,
        help_text="Reason for renewal"
    )
    
    def validate_new_expiration_date(self, value):
        """Validate that new expiration date is in the future."""
        if value <= timezone.now():
            raise serializers.ValidationError("New expiration date must be in the future.")
        return value


class LicenseSuspensionSerializer(serializers.Serializer):
    """Serializer for license suspension requests."""
    
    reason = serializers.CharField(
        max_length=500,
        help_text="Reason for suspension"
    )


class LicenseCancellationSerializer(serializers.Serializer):
    """Serializer for license cancellation requests."""
    
    reason = serializers.CharField(
        max_length=500,
        help_text="Reason for cancellation"
    )


class ActivationDeactivationSerializer(serializers.Serializer):
    """Serializer for activation deactivation requests."""
    
    reason = serializers.CharField(
        max_length=500,
        required=False,
        help_text="Reason for deactivation"
    )


class LicenseActivationSerializer(serializers.Serializer):
    """Serializer for license activation requests."""
    
    license_key = serializers.CharField(max_length=255)
    product_slug = serializers.CharField(max_length=100)
    instance_identifier = serializers.CharField(max_length=500)
    instance_type = serializers.CharField(max_length=100, required=False, default='website')
    
    def validate_license_key(self, value):
        """Validate license key format."""
        if not value or len(value) < 10:
            raise serializers.ValidationError("Invalid license key format.")
        return value
