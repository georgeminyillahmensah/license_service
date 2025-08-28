"""
Pytest configuration and fixtures for Centralized License Service
"""
import pytest
from django.test import Client
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
# JWT tokens not needed for basic testing
from licenses.models import Brand, Product, LicenseKey, License, Activation
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


@pytest.fixture
def api_client():
    """API client for testing REST endpoints."""
    return APIClient()


@pytest.fixture
def client():
    """Django test client for testing views."""
    return Client()


@pytest.fixture
def admin_user():
    """Create and return an admin user."""
    user = User.objects.create_user(
        username='testadmin',
        email='test@example.com',
        password='testpass123',
        is_staff=True,
        is_superuser=True
    )
    return user


@pytest.fixture
def regular_user():
    """Create and return a regular user."""
    user = User.objects.create_user(
        username='testuser',
        email='user@test.com',
        password='testpass123'
    )
    return user


@pytest.fixture
def authenticated_client(admin_user, client):
    """Return an authenticated Django test client."""
    client.force_login(admin_user)
    return client


@pytest.fixture
def authenticated_api_client(admin_user, api_client):
    """Return an authenticated API client."""
    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.fixture
def brand():
    """Create and return a test brand."""
    return Brand.objects.create(
        name='Test Brand',
        slug='test-brand',
        description='Test brand for testing'
    )


@pytest.fixture
def product(brand):
    """Create and return a test product."""
    return Product.objects.create(
        name='Test Product',
        description='Test product for testing',
        slug='test-product',
        brand=brand
    )


@pytest.fixture
def license_key(brand):
    """Create and return a test license key."""
    return LicenseKey.objects.create(
        key='TEST-LICENSE-KEY-12345',
        brand=brand,
        customer_email='test@example.com'
    )


@pytest.fixture
def license(license_key, product):
    """Create and return a test license."""
    return License.objects.create(
        license_key=license_key,
        product=product,
        seats=5,
        expiration_date=timezone.now() + timedelta(days=365)
    )


@pytest.fixture
def activation(license):
    """Create and return a test activation."""
    return Activation.objects.create(
        license=license,
        instance_identifier='https://test.example.com',
        instance_type='website'
    )


@pytest.fixture
def multiple_activations(license):
    """Create and return multiple test activations."""
    activations = []
    for i in range(3):
        activation = Activation.objects.create(
            license=license,
            instance_identifier=f'https://test{i}.example.com',
            instance_type='website'
        )
        activations.append(activation)
    return activations


@pytest.fixture
def expired_license(license_key, product):
    """Create and return an expired test license."""
    return License.objects.create(
        license_key=license_key,
        product=product,
        seats=3,
        expiration_date=timezone.now() - timedelta(days=1)
    )


@pytest.fixture
def suspended_license(license_key, product):
    """Create and return a suspended test license."""
    license = License.objects.create(
        license_key=license_key,
        product=product,
        seats=2,
        expiration_date=timezone.now() + timedelta(days=30)
    )
    license.suspend('Testing suspension')
    return license


@pytest.fixture
def cancelled_license(license_key, product):
    """Create and return a cancelled test license."""
    license = License.objects.create(
        license_key=license_key,
        product=product,
        seats=2,
        expiration_date=timezone.now() + timedelta(days=30)
    )
    license.cancel('Testing cancellation')
    return license


@pytest.fixture
def sample_data(brand, product, license_key, license, multiple_activations):
    """Create and return a complete set of sample data."""
    return {
        'brand': brand,
        'product': product,
        'license_key': license_key,
        'license': license,
        'activations': multiple_activations
    }


@pytest.fixture
def api_headers():
    """Return common API headers."""
    return {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }


@pytest.fixture
def license_data():
    """Return sample license data for testing."""
    return {
        'license_key': 1,
        'product': 1,
        'seats': 3,
        'expiration_date': (timezone.now() + timedelta(days=365)).strftime('%Y-%m-%d %H:%M:%S')
    }


@pytest.fixture
def activation_data():
    """Return sample activation data for testing."""
    return {
        'license': 1,
        'instance_identifier': 'https://newtest.example.com',
        'instance_type': 'website'
    }


@pytest.fixture
def renewal_data():
    """Return sample renewal data for testing."""
    return {
        'new_expiration_date': timezone.now() + timedelta(days=30),
        'reason': 'Testing renewal'
    }


@pytest.fixture
def suspension_data():
    """Return sample suspension data for testing."""
    return {
        'reason': 'Testing suspension functionality'
    }


@pytest.fixture
def cancellation_data():
    """Return sample cancellation data for testing."""
    return {
        'reason': 'Testing cancellation functionality'
    }


@pytest.fixture
def deactivation_data():
    """Return sample deactivation data for testing."""
    return {
        'reason': 'Testing deactivation functionality'
    }


@pytest.fixture
def bulk_deactivation_data():
    """Return sample bulk deactivation data for testing."""
    return {
        'activation_ids': [1, 2],
        'reason': 'Testing bulk deactivation'
    }


# Database transaction fixtures
@pytest.fixture(scope='function')
def db_transaction():
    """Ensure database transaction for each test."""
    pass


@pytest.fixture(scope='class')
def db_transaction_class():
    """Ensure database transaction for each test class."""
    pass


# Performance testing fixtures
@pytest.fixture
def large_dataset(brand, product):
    """Create a large dataset for performance testing."""
    # Create multiple license keys
    license_keys = []
    for i in range(10):
        license_key = LicenseKey.objects.create(
            key=f'PERF-LICENSE-KEY-{i:04d}',
            brand=brand,
            customer_email=f'perfcustomer{i}@test.com'
        )
        license_keys.append(license_key)
    
    # Create multiple licenses
    licenses = []
    for i, license_key in enumerate(license_keys):
        license = License.objects.create(
            license_key=license_key,
            product=product,
            seats=8,
            expiration_date=timezone.now() + timedelta(days=365)
        )
        licenses.append(license)
    
    # Create multiple activations
    activations = []
    for license in licenses:
        for j in range(5):
            activation = Activation.objects.create(
                license=license,
                instance_identifier=f'https://perftest{j}.example.com',
                instance_type='website'
            )
            activations.append(activation)
    
    return {
        'license_keys': license_keys,
        'licenses': licenses,
        'activations': activations
    }
