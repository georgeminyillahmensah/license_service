from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, PermissionDenied
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiExample
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from .models import Brand, Product, LicenseKey, License, Activation
from .serializers import (
    BrandSerializer, ProductSerializer, LicenseKeySerializer, LicenseSerializer,
    ActivationSerializer, LicenseKeyDetailSerializer, LicenseStatusSerializer,
    LicenseActivationSerializer, LicenseRenewalSerializer, LicenseSuspensionSerializer,
    LicenseCancellationSerializer, ActivationDeactivationSerializer
)
import logging

logger = logging.getLogger(__name__)


class BrandViewSet(viewsets.ModelViewSet):
    """ViewSet for Brand management."""
    
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['is_active']
    search_fields = ['name', 'slug', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    def get_queryset(self):
        """Filter queryset based on user permissions."""
        if self.request.user.is_license_admin or self.request.user.is_staff:
            return Brand.objects.all()
        # Regular users can only see active brands
        return Brand.objects.filter(is_active=True)


class ProductViewSet(viewsets.ModelViewSet):
    """ViewSet for Product management."""
    
    queryset = Product.objects.select_related('brand')
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['brand', 'is_active']
    search_fields = ['name', 'slug', 'description', 'brand__name']
    ordering_fields = ['name', 'brand__name', 'created_at']
    ordering = ['brand__name', 'name']
    
    def get_queryset(self):
        """Filter queryset based on user permissions."""
        if self.request.user.is_license_admin or self.request.user.is_staff:
            return Product.objects.select_related('brand')
        # Regular users can only see active products from active brands
        return Product.objects.filter(
            is_active=True, 
            brand__is_active=True
        ).select_related('brand')


class LicenseKeyViewSet(viewsets.ModelViewSet):
    """ViewSet for LicenseKey management."""
    
    queryset = LicenseKey.objects.select_related('brand').prefetch_related('licenses')
    serializer_class = LicenseKeySerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['brand', 'is_active', 'customer_email']
    search_fields = ['key', 'customer_email', 'brand__name']
    ordering_fields = ['created_at', 'customer_email']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Use detailed serializer for retrieve actions."""
        if self.action in ['retrieve', 'list']:
            return LicenseKeyDetailSerializer
        return LicenseKeySerializer
    
    def get_queryset(self):
        """Filter queryset based on user permissions."""
        if self.request.user.is_license_admin or self.request.user.is_staff:
            return LicenseKey.objects.select_related('brand').prefetch_related('licenses')
        # Regular users can only see their own license keys
        return LicenseKey.objects.filter(
            customer_email=self.request.user.email
        ).select_related('brand').prefetch_related('licenses')
    
    @action(detail=False, methods=['get'])
    def by_email(self, request):
        """Get all licenses by customer email across all brands (US6)."""
        if not (request.user.is_license_admin or request.user.is_staff):
            raise PermissionDenied("Only license admins can access this endpoint.")
        
        email = request.query_params.get('email')
        if not email:
            raise ValidationError("Email parameter is required.")
        
        license_keys = LicenseKey.objects.filter(
            customer_email=email
        ).select_related('brand').prefetch_related('licenses__product__brand')
        
        serializer = LicenseKeyDetailSerializer(license_keys, many=True)
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(
        summary="List all licenses",
        description="Retrieve a list of all licenses with filtering and pagination",
        tags=['licenses']
    ),
    create=extend_schema(
        summary="Create a new license",
        description="Create a new license for a product",
        tags=['licenses']
    ),
    retrieve=extend_schema(
        summary="Retrieve a license",
        description="Get detailed information about a specific license",
        tags=['licenses']
    ),
    update=extend_schema(
        summary="Update a license",
        description="Update license information",
        tags=['licenses']
    ),
    destroy=extend_schema(
        summary="Delete a license",
        description="Delete a license (soft delete)",
        tags=['licenses']
    )
)
class LicenseViewSet(viewsets.ModelViewSet):
    """ViewSet for License management."""
    
    queryset = License.objects.select_related('license_key__brand', 'product__brand')
    serializer_class = LicenseSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['status', 'product', 'license_key__brand']
    search_fields = ['product__name', 'license_key__customer_email']
    ordering_fields = ['created_at', 'expiration_date']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter queryset based on user permissions."""
        if self.request.user.is_license_admin or self.request.user.is_staff:
            return License.objects.select_related('license_key__brand', 'product__brand')
        # Regular users can only see their own licenses
        return License.objects.filter(
            license_key__customer_email=self.request.user.email
        ).select_related('license_key__brand', 'product__brand')
    
    @extend_schema(
        summary="Renew a license",
        description="Extend the expiration date of a license",
        request=LicenseRenewalSerializer,
        responses={
            200: {
                'description': 'License renewed successfully',
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean'},
                    'message': {'type': 'string'},
                    'license': {'type': 'object'}
                }
            },
            400: {'description': 'Invalid request or license cannot be renewed'}
        },
        tags=['licenses']
    )
    @action(detail=True, methods=['post'])
    def renew(self, request, pk=None):
        """Renew a license (US2 - full implementation)."""
        license_obj = self.get_object()
        serializer = LicenseRenewalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            license_obj.renew(
                new_expiration_date=serializer.validated_data['new_expiration_date'],
                reason=serializer.validated_data.get('reason')
            )
            
            logger.info(
                f"License {license_obj.id} renewed by user {request.user.username} "
                f"until {serializer.validated_data['new_expiration_date']}"
            )
            
            result_serializer = self.get_serializer(license_obj)
            return Response({
                'success': True,
                'message': 'License renewed successfully',
                'license': result_serializer.data
            })
            
        except ValueError as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def suspend(self, request, pk=None):
        """Suspend a license (US2 - full implementation)."""
        license_obj = self.get_object()
        serializer = LicenseSuspensionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            license_obj.suspend(reason=serializer.validated_data['reason'])
            
            logger.info(
                f"License {license_obj.id} suspended by user {request.user.username}: "
                f"{serializer.validated_data['reason']}"
            )
            
            result_serializer = self.get_serializer(license_obj)
            return Response({
                'success': True,
                'message': 'License suspended successfully',
                'license': result_serializer.data
            })
            
        except ValueError as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def resume(self, request, pk=None):
        """Resume a suspended license (US2 - full implementation)."""
        license_obj = self.get_object()
        
        try:
            license_obj.resume()
            
            logger.info(
                f"License {license_obj.id} resumed by user {request.user.username}"
            )
            
            result_serializer = self.get_serializer(license_obj)
            return Response({
                'success': True,
                'message': 'License resumed successfully',
                'license': result_serializer.data
            })
            
        except ValueError as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a license (US2 - full implementation)."""
        license_obj = self.get_object()
        serializer = LicenseCancellationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            license_obj.cancel(reason=serializer.validated_data['reason'])
            
            logger.info(
                f"License {license_obj.id} cancelled by user {request.user.username}: "
                f"{serializer.validated_data['reason']}"
            )
            
            result_serializer = self.get_serializer(license_obj)
            return Response({
                'success': True,
                'message': 'License cancelled successfully',
                'license': result_serializer.data
            })
            
        except ValueError as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def change_status(self, request, pk=None):
        """Change license status (legacy method - kept for backward compatibility)."""
        license_obj = self.get_object()
        new_status = request.data.get('status')
        
        if new_status not in dict(License.STATUS_CHOICES):
            raise ValidationError("Invalid status value.")
        
        # Log the status change
        logger.info(
            f"License {license_obj.id} status changed from {license_obj.status} to {new_status} "
            f"by user {request.user.username}"
        )
        
        license_obj.status = new_status
        license_obj.save()
        
        serializer = self.get_serializer(license_obj)
        return Response(serializer.data)


class ActivationViewSet(viewsets.ModelViewSet):
    """ViewSet for Activation management."""
    
    queryset = Activation.objects.select_related('license__product__brand', 'license__license_key')
    serializer_class = ActivationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['is_active', 'instance_type', 'license__product__brand']
    search_fields = ['instance_identifier', 'license__product__name']
    ordering_fields = ['activated_at']
    ordering = ['-activated_at']
    
    def get_queryset(self):
        """Filter queryset based on user permissions."""
        if self.request.user.is_license_admin or self.request.user.is_staff:
            return Activation.objects.select_related('license__product__brand', 'license__license_key')
        # Regular users can only see their own activations
        return Activation.objects.filter(
            license__license_key__customer_email=self.request.user.email
        ).select_related('license__product__brand', 'license__license_key')
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate a specific activation (US5 - full implementation)."""
        activation = self.get_object()
        
        if not activation.is_active:
            raise ValidationError("Activation is already deactivated.")
        
        serializer = ActivationDeactivationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            activation.deactivate(reason=serializer.validated_data.get('reason'))
            
            logger.info(
                f"Activation {activation.id} deactivated by user {request.user.username} "
                f"for instance {activation.instance_identifier}"
            )
            
            result_serializer = self.get_serializer(activation)
            return Response({
                'success': True,
                'message': 'Activation deactivated successfully',
                'activation': result_serializer.data
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def bulk_deactivate(self, request):
        """Bulk deactivate multiple activations (US5 - enhanced feature)."""
        activation_ids = request.data.get('activation_ids', [])
        reason = request.data.get('reason', '')
        
        if not activation_ids:
            return Response({
                'success': False,
                'error': 'No activation IDs provided'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        deactivated_count = 0
        errors = []
        
        for activation_id in activation_ids:
            try:
                activation = Activation.objects.get(
                    id=activation_id,
                    license__license_key__customer_email=request.user.email
                )
                
                if activation.is_active:
                    activation.deactivate(reason=reason)
                    deactivated_count += 1
                    
                    logger.info(
                        f"Activation {activation.id} bulk deactivated by user {request.user.username}"
                    )
                else:
                    errors.append(f"Activation {activation_id} is already deactivated")
                    
            except Activation.DoesNotExist:
                errors.append(f"Activation {activation_id} not found or access denied")
            except Exception as e:
                errors.append(f"Error deactivating activation {activation_id}: {str(e)}")
        
        return Response({
            'success': True,
            'message': f'Successfully deactivated {deactivated_count} activations',
            'deactivated_count': deactivated_count,
            'errors': errors
        })


class LicenseServiceViewSet(viewsets.ViewSet):
    """ViewSet for core license service operations."""
    
    permission_classes = [permissions.AllowAny]  # Allow anonymous access for license checks
    
    @action(detail=False, methods=['post'])
    def check_status(self, request):
        """Check license status and entitlements (US4)."""
        serializer = LicenseStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        license_key = serializer.validated_data['license_key']
        product_slug = serializer.validated_data.get('product_slug')
        instance_identifier = serializer.validated_data.get('instance_identifier')
        
        try:
            license_key_obj = LicenseKey.objects.get(key=license_key, is_active=True)
        except ObjectDoesNotExist:
            return Response({
                'valid': False,
                'error': 'Invalid or inactive license key'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get all valid licenses for this key
        licenses = license_key_obj.licenses.filter(
            status='valid',
            expiration_date__gt=timezone.now()
        ).select_related('product')
        
        if product_slug:
            licenses = licenses.filter(product__slug=product_slug)
        
        if not licenses.exists():
            return Response({
                'valid': False,
                'error': 'No valid licenses found for this key'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check instance-specific activation if provided
        instance_info = None
        if instance_identifier:
            activation = Activation.objects.filter(
                license__in=licenses,
                instance_identifier=instance_identifier,
                is_active=True
            ).first()
            
            if activation:
                instance_info = {
                    'instance_identifier': activation.instance_identifier,
                    'instance_type': activation.instance_type,
                    'activated_at': activation.activated_at
                }
        
        # Build response
        response_data = {
            'valid': True,
            'license_key': license_key,
            'customer_email': license_key_obj.customer_email,
            'brand': license_key_obj.brand.name,
            'licenses': []
        }
        
        for license_obj in licenses:
            license_data = {
                'product': license_obj.product.name,
                'product_slug': license_obj.product.slug,
                'status': license_obj.status,
                'seats': license_obj.seats,
                'available_seats': license_obj.available_seats,
                'expiration_date': license_obj.expiration_date,
                'is_expired': license_obj.is_expired
            }
            
            if instance_identifier:
                license_data['instance_info'] = instance_info
            
            response_data['licenses'].append(license_data)
        
        return Response(response_data)
    
    @action(detail=False, methods=['post'])
    def activate(self, request):
        """Activate a license for a specific instance (US3)."""
        serializer = LicenseActivationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        license_key = serializer.validated_data['license_key']
        product_slug = serializer.validated_data['product_slug']
        instance_identifier = serializer.validated_data['instance_identifier']
        instance_type = serializer.validated_data['instance_type']
        
        try:
            license_key_obj = LicenseKey.objects.get(key=license_key, is_active=True)
        except ObjectDoesNotExist:
            return Response({
                'success': False,
                'error': 'Invalid or inactive license key'
            }, status=status.HTTP_404_NOT_FOUND)
        
        try:
            license_obj = license_key_obj.licenses.get(
                product__slug=product_slug,
                status='valid',
                expiration_date__gt=timezone.now()
            )
        except ObjectDoesNotExist:
            return Response({
                'success': False,
                'error': 'No valid license found for this product'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if activation already exists
        existing_activation = Activation.objects.filter(
            license=license_obj,
            instance_identifier=instance_identifier,
            is_active=True
        ).first()
        
        if existing_activation:
            return Response({
                'success': True,
                'message': 'License already activated for this instance',
                'activation_id': existing_activation.id
            })
        
        # Check seat availability
        if license_obj.available_seats <= 0:
            return Response({
                'success': False,
                'error': 'No available seats for this license'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create activation
        with transaction.atomic():
            activation = Activation.objects.create(
                license=license_obj,
                instance_identifier=instance_identifier,
                instance_type=instance_type
            )
            
            logger.info(
                f"License {license_obj.id} activated for instance {instance_identifier} "
                f"by license key {license_key}"
            )
        
        return Response({
            'success': True,
            'message': 'License activated successfully',
            'activation_id': activation.id,
            'available_seats': license_obj.available_seats - 1
        })
    
    @action(detail=False, methods=['post'])
    def provision(self, request):
        """Provision a new license (US1 - Brand API)."""
        # This endpoint is for brand systems to create licenses
        if not (request.user.is_authenticated and 
                (request.user.is_license_admin or request.user.is_staff)):
            raise PermissionDenied("Only license admins can provision licenses.")
        
        customer_email = request.data.get('customer_email')
        brand_id = request.data.get('brand_id')
        product_id = request.data.get('product_id')
        seats = request.data.get('seats', 1)
        expiration_date = request.data.get('expiration_date')
        
        if not all([customer_email, brand_id, product_id, expiration_date]):
            raise ValidationError("Missing required fields: customer_email, brand_id, product_id, expiration_date")
        
        try:
            brand = Brand.objects.get(id=brand_id, is_active=True)
            product = Product.objects.get(id=product_id, brand=brand, is_active=True)
        except ObjectDoesNotExist:
            raise ValidationError("Invalid brand or product")
        
        with transaction.atomic():
            # Create or get existing license key for this customer and brand
            license_key, created = LicenseKey.objects.get_or_create(
                customer_email=customer_email,
                brand=brand,
                defaults={'is_active': True}
            )
            
            # Create the license
            license_obj = License.objects.create(
                license_key=license_key,
                product=product,
                seats=seats,
                expiration_date=expiration_date,
                status='valid'
            )
            
            logger.info(
                f"License provisioned: {license_obj.id} for {customer_email} "
                f"on product {product.name} by user {request.user.username}"
            )
        
        return Response({
            'success': True,
            'license_key': license_key.key,
            'license_id': license_obj.id,
            'message': 'License provisioned successfully'
        }, status=status.HTTP_201_CREATED)
