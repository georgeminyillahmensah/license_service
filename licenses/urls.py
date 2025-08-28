from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router for ViewSets
router = DefaultRouter()
router.register(r'brands', views.BrandViewSet)
router.register(r'products', views.ProductViewSet)
router.register(r'license-keys', views.LicenseKeyViewSet)
router.register(r'licenses', views.LicenseViewSet)
router.register(r'activations', views.ActivationViewSet)
router.register(r'service', views.LicenseServiceViewSet, basename='license-service')

app_name = 'licenses'

urlpatterns = [
    # Include router URLs
    path('api/', include(router.urls)),
    
    # Additional custom endpoints
    path('api/license-keys/by-email/', views.LicenseKeyViewSet.as_view({
        'get': 'by_email'
    }), name='license-keys-by-email'),
]
