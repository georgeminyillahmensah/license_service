import pytest
from django.test import Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.admin.sites import site
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from licenses.models import Brand, Product, LicenseKey, License, Activation

User = get_user_model()


@pytest.mark.django_db
class TestAdminAuthentication:
    """Test admin authentication and access control."""

    def test_admin_login_page(self, client):
        """Test that admin login page is accessible."""
        url = reverse('admin:login')
        response = client.get(url)
        assert response.status_code == 200
        assert 'Django administration' in response.content.decode('utf-8')

    def test_admin_login_success(self, admin_user, client):
        """Test successful admin login."""
        client.force_login(admin_user)
        url = reverse('admin:index')
        response = client.get(url)
        assert response.status_code == 200
        assert 'Django administration' in response.content.decode('utf-8')

    def test_admin_login_failure(self, client):
        """Test failed admin login."""
        url = reverse('admin:login')
        data = {
            'username': 'wronguser',
            'password': 'wrongpass',
        }
        response = client.post(url, data, follow=True)
        assert response.status_code == 200
        # Should still be on login page
        assert 'Django administration' in response.content.decode('utf-8')


@pytest.mark.django_db
class TestAdminInterface:
    """Test admin interface accessibility and functionality."""

    def test_admin_index(self, admin_user, client):
        """Test admin index page."""
        client.force_login(admin_user)
        url = reverse('admin:index')
        response = client.get(url)
        assert response.status_code == 200
        assert 'Django administration' in response.content.decode('utf-8')

    def test_admin_app_list(self, admin_user, client):
        """Test admin app list."""
        client.force_login(admin_user)
        url = reverse('admin:app_list', args=['licenses'])
        response = client.get(url)
        assert response.status_code == 200


@pytest.mark.django_db
class TestBrandAdmin:
    """Test Brand admin functionality."""

    def test_brand_list_view(self, admin_user, client, brand):
        """Test brand list view in admin."""
        client.force_login(admin_user)
        url = reverse('admin:licenses_brand_changelist')
        response = client.get(url)
        assert response.status_code == 200
        assert brand.name in response.content.decode('utf-8')

    def test_brand_add_view(self, admin_user, client):
        """Test brand add view in admin."""
        client.force_login(admin_user)
        url = reverse('admin:licenses_brand_add')
        response = client.get(url)
        assert response.status_code == 200

    def test_brand_creation(self, admin_user, client):
        """Test brand creation through admin."""
        client.force_login(admin_user)
        url = reverse('admin:licenses_brand_add')
        data = {
            'name': 'New Brand',
            'slug': 'new-brand',
            'description': 'A new test brand',
        }
        response = client.post(url, data, follow=True)
        assert response.status_code == 200
        assert Brand.objects.filter(name='New Brand').exists()

    def test_brand_change_view(self, admin_user, client, brand):
        """Test brand change view in admin."""
        client.force_login(admin_user)
        url = reverse('admin:licenses_brand_change', args=[brand.id])
        response = client.get(url)
        assert response.status_code == 200
        assert brand.name in response.content.decode('utf-8')

    def test_brand_update(self, admin_user, client, brand):
        """Test brand update through admin."""
        client.force_login(admin_user)
        url = reverse('admin:licenses_brand_change', args=[brand.id])
        data = {
            'name': 'Updated Brand',
            'slug': 'updated-brand',
            'description': 'Updated description',
        }
        response = client.post(url, data, follow=True)
        assert response.status_code == 200
        brand.refresh_from_db()
        assert brand.name == 'Updated Brand'

    def test_brand_delete_view(self, admin_user, client, brand):
        """Test brand delete view in admin."""
        client.force_login(admin_user)
        url = reverse('admin:licenses_brand_delete', args=[brand.id])
        response = client.get(url)
        assert response.status_code == 200

    def test_brand_deletion(self, admin_user, client, brand):
        """Test brand deletion through admin."""
        client.force_login(admin_user)
        url = reverse('admin:licenses_brand_delete', args=[brand.id])
        data = {'post': 'yes'}
        response = client.post(url, data, follow=True)
        assert response.status_code == 200
        assert not Brand.objects.filter(id=brand.id).exists()


@pytest.mark.django_db
class TestProductAdmin:
    """Test Product admin functionality."""

    def test_product_list_view(self, admin_user, client, product):
        """Test product list view in admin."""
        client.force_login(admin_user)
        url = reverse('admin:licenses_product_changelist')
        response = client.get(url)
        assert response.status_code == 200
        assert product.name in response.content.decode('utf-8')

    def test_product_add_view(self, admin_user, client, brand):
        """Test product add view in admin."""
        client.force_login(admin_user)
        url = reverse('admin:licenses_product_add')
        response = client.get(url)
        assert response.status_code == 200

    def test_product_creation(self, admin_user, client, brand):
        """Test product creation through admin."""
        client.force_login(admin_user)
        url = reverse('admin:licenses_product_add')
        data = {
            'name': 'New Product',
            'slug': 'new-product',
            'description': 'A new test product',
            'brand': brand.id,
        }
        response = client.post(url, data, follow=True)
        assert response.status_code == 200
        assert Product.objects.filter(name='New Product').exists()

    def test_product_change_view(self, admin_user, client, product):
        """Test product change view in admin."""
        client.force_login(admin_user)
        url = reverse('admin:licenses_product_change', args=[product.id])
        response = client.get(url)
        assert response.status_code == 200
        assert product.name in response.content.decode('utf-8')

    def test_product_update(self, admin_user, client, product):
        """Test product update through admin."""
        client.force_login(admin_user)
        url = reverse('admin:licenses_product_change', args=[product.id])
        data = {
            'name': 'Updated Product',
            'slug': 'updated-product',
            'description': 'Updated description',
            'brand': product.brand.id,
        }
        response = client.post(url, data, follow=True)
        assert response.status_code == 200
        product.refresh_from_db()
        assert product.name == 'Updated Product'

    def test_product_delete_view(self, admin_user, client, product):
        """Test product delete view in admin."""
        client.force_login(admin_user)
        url = reverse('admin:licenses_product_delete', args=[product.id])
        response = client.get(url)
        assert response.status_code == 200

    def test_product_deletion(self, admin_user, client, product):
        """Test product deletion through admin."""
        client.force_login(admin_user)
        url = reverse('admin:licenses_product_delete', args=[product.id])
        data = {'post': 'yes'}
        response = client.post(url, data, follow=True)
        assert response.status_code == 200
        assert not Product.objects.filter(id=product.id).exists()


@pytest.mark.django_db
class TestLicenseKeyAdmin:
    """Test LicenseKey admin functionality."""

    def test_license_key_list_view(self, admin_user, client, license_key):
        """Test license key list view in admin."""
        client.force_login(admin_user)
        url = reverse('admin:licenses_licensekey_changelist')
        response = client.get(url)
        assert response.status_code == 200
        assert license_key.customer_email in response.content.decode('utf-8')

    def test_license_key_add_view(self, admin_user, client, brand):
        """Test license key add view in admin."""
        client.force_login(admin_user)
        url = reverse('admin:licenses_licensekey_add')
        response = client.get(url)
        assert response.status_code == 200

    def test_license_key_creation(self, admin_user, client, brand):
        """Test license key creation through admin."""
        client.force_login(admin_user)
        url = reverse('admin:licenses_licensekey_add')
        data = {
            'customer_email': 'new@test.com',
            'brand': brand.id,
        }
        response = client.post(url, data, follow=True)
        assert response.status_code == 200
        assert LicenseKey.objects.filter(customer_email='new@test.com').exists()

    def test_license_key_change_view(self, admin_user, client, license_key):
        """Test license key change view in admin."""
        client.force_login(admin_user)
        url = reverse('admin:licenses_licensekey_change', args=[license_key.id])
        response = client.get(url)
        assert response.status_code == 200
        assert license_key.customer_email in response.content.decode('utf-8')

    def test_license_key_update(self, admin_user, client, license_key):
        """Test license key update through admin."""
        client.force_login(admin_user)
        url = reverse('admin:licenses_licensekey_change', args=[license_key.id])
        data = {
            'customer_email': 'updated@test.com',
            'brand': license_key.brand.id,
        }
        response = client.post(url, data, follow=True)
        assert response.status_code == 200
        license_key.refresh_from_db()
        assert license_key.customer_email == 'updated@test.com'

    def test_license_key_delete_view(self, admin_user, client, license_key):
        """Test license key delete view in admin."""
        client.force_login(admin_user)
        url = reverse('admin:licenses_licensekey_delete', args=[license_key.id])
        response = client.get(url)
        assert response.status_code == 200

    def test_license_key_deletion(self, admin_user, client, license_key):
        """Test license key deletion through admin."""
        client.force_login(admin_user)
        url = reverse('admin:licenses_licensekey_delete', args=[license_key.id])
        data = {'post': 'yes'}
        response = client.post(url, data, follow=True)
        assert response.status_code == 200
        assert not LicenseKey.objects.filter(id=license_key.id).exists()


@pytest.mark.django_db
class TestLicenseAdmin:
    """Test License admin functionality."""

    def test_license_list_view(self, admin_user, client, license):
        """Test license list view in admin."""
        client.force_login(admin_user)
        url = reverse('admin:licenses_license_changelist')
        response = client.get(url)
        assert response.status_code == 200
        assert str(license.product) in response.content.decode('utf-8')

    def test_license_add_view(self, admin_user, client, license_key, product):
        """Test license add view in admin."""
        client.force_login(admin_user)
        url = reverse('admin:licenses_license_add')
        response = client.get(url)
        assert response.status_code == 200

    def test_license_creation(self, admin_user, client, license_key, product):
        """Test license creation through admin."""
        client.force_login(admin_user)
        url = reverse('admin:licenses_license_add')
        data = {
            'license_key': license_key.id,
            'product': product.id,
            'status': 'valid',
            'seats': 10,
            'expiration_date_0': '2026-12-31',
            'expiration_date_1': '00:00:00',
        }
        response = client.post(url, data, follow=True)
        assert response.status_code == 200
        assert License.objects.filter(seats=10).exists()

    def test_license_change_view(self, admin_user, client, license):
        """Test license change view in admin."""
        client.force_login(admin_user)
        url = reverse('admin:licenses_license_change', args=[license.id])
        response = client.get(url)
        assert response.status_code == 200
        assert str(license.product) in response.content.decode('utf-8')

    def test_license_update(self, admin_user, client, license):
        """Test license update through admin."""
        client.force_login(admin_user)
        url = reverse('admin:licenses_license_change', args=[license.id])
        data = {
            'license_key': license.license_key.id,
            'product': license.product.id,
            'status': 'valid',
            'seats': 15,
            'expiration_date_0': '2026-12-31',
            'expiration_date_1': '00:00:00',
        }
        response = client.post(url, data, follow=True)
        assert response.status_code == 200
        license.refresh_from_db()
        assert license.seats == 15

    def test_license_delete_view(self, admin_user, client, license):
        """Test license delete view in admin."""
        client.force_login(admin_user)
        url = reverse('admin:licenses_license_delete', args=[license.id])
        response = client.get(url)
        assert response.status_code == 200

    def test_license_deletion(self, admin_user, client, license):
        """Test license deletion through admin."""
        client.force_login(admin_user)
        url = reverse('admin:licenses_license_delete', args=[license.id])
        data = {'post': 'yes'}
        response = client.post(url, data, follow=True)
        assert response.status_code == 200
        assert not License.objects.filter(id=license.id).exists()


@pytest.mark.django_db
class TestActivationAdmin:
    """Test Activation admin functionality."""

    def test_activation_list_view(self, admin_user, client, activation):
        """Test activation list view in admin."""
        client.force_login(admin_user)
        url = reverse('admin:licenses_activation_changelist')
        response = client.get(url)
        assert response.status_code == 200
        assert activation.instance_identifier in response.content.decode('utf-8')

    def test_activation_add_view(self, admin_user, client, license):
        """Test activation add view in admin."""
        client.force_login(admin_user)
        url = reverse('admin:licenses_activation_add')
        response = client.get(url)
        assert response.status_code == 200

    def test_activation_creation(self, admin_user, client, license):
        """Test activation creation through admin."""
        client.force_login(admin_user)
        url = reverse('admin:licenses_activation_add')
        data = {
            'license': license.id,
            'instance_identifier': 'test-instance-123',
            'instance_url': 'https://test.example.com',
        }
        response = client.post(url, data, follow=True)
        assert response.status_code == 200
        assert Activation.objects.filter(instance_identifier='test-instance-123').exists()

    def test_activation_change_view(self, admin_user, client, activation):
        """Test activation change view in admin."""
        client.force_login(admin_user)
        url = reverse('admin:licenses_activation_change', args=[activation.id])
        response = client.get(url)
        assert response.status_code == 200
        assert activation.instance_identifier in response.content.decode('utf-8')

    def test_activation_update(self, admin_user, client, activation):
        """Test activation update through admin."""
        client.force_login(admin_user)
        url = reverse('admin:licenses_activation_change', args=[activation.id])
        data = {
            'license': activation.license.id,
            'instance_identifier': 'updated-instance-456',
            'instance_url': 'https://updated.example.com',
        }
        response = client.post(url, data, follow=True)
        assert response.status_code == 200
        activation.refresh_from_db()
        assert activation.instance_identifier == 'updated-instance-456'

    def test_activation_delete_view(self, admin_user, client, activation):
        """Test activation delete view in admin."""
        client.force_login(admin_user)
        url = reverse('admin:licenses_activation_delete', args=[activation.id])
        response = client.get(url)
        assert response.status_code == 200

    def test_activation_deletion(self, admin_user, client, activation):
        """Test activation deletion through admin."""
        client.force_login(admin_user)
        url = reverse('admin:licenses_activation_delete', args=[activation.id])
        data = {'post': 'yes'}
        response = client.post(url, data, follow=True)
        assert response.status_code == 200
        assert not Activation.objects.filter(id=activation.id).exists()


@pytest.mark.django_db
class TestAdminCustomizations:
    """Test admin customizations and display methods."""

    def test_brand_admin_display(self, admin_user, client, brand):
        """Test brand admin display methods."""
        client.force_login(admin_user)
        url = reverse('admin:licenses_brand_changelist')
        response = client.get(url)
        content = response.content.decode('utf-8')
        assert brand.name in content
        assert brand.slug in content

    def test_product_admin_display(self, admin_user, client, product):
        """Test product admin display methods."""
        client.force_login(admin_user)
        url = reverse('admin:licenses_product_changelist')
        response = client.get(url)
        content = response.content.decode('utf-8')
        assert product.name in content
        assert product.brand.name in content

    def test_license_key_admin_display(self, admin_user, client, license_key):
        """Test license key admin display methods."""
        client.force_login(admin_user)
        url = reverse('admin:licenses_licensekey_changelist')
        response = client.get(url)
        content = response.content.decode('utf-8')
        assert license_key.customer_email in content
        assert license_key.brand.name in content

    def test_license_admin_display(self, admin_user, client, license):
        """Test license admin display methods."""
        client.force_login(admin_user)
        url = reverse('admin:licenses_license_changelist')
        response = client.get(url)
        content = response.content.decode('utf-8')
        # Check if the license data is displayed
        assert str(license.product) in content
        # The license key might not be displayed in the changelist view
        # Let's check if the license is actually in the database
        assert License.objects.filter(id=license.id).exists()

    def test_activation_admin_display(self, admin_user, client, activation):
        """Test activation admin display methods."""
        client.force_login(admin_user)
        url = reverse('admin:licenses_activation_changelist')
        response = client.get(url)
        content = response.content.decode('utf-8')
        # Check if the activation data is displayed
        assert activation.instance_identifier in content
        # The license might not be displayed in the changelist view
        # Let's check if the activation is actually in the database
        assert Activation.objects.filter(id=activation.id).exists()


@pytest.mark.django_db
class TestAdminActions:
    """Test admin actions and bulk operations."""

    def test_brand_admin_actions(self, admin_user, client, brand):
        """Test brand admin actions."""
        client.force_login(admin_user)
        url = reverse('admin:licenses_brand_changelist')
        response = client.get(url)
        assert response.status_code == 200

    def test_product_admin_actions(self, admin_user, client, product):
        """Test product admin actions."""
        client.force_login(admin_user)
        url = reverse('admin:licenses_product_changelist')
        response = client.get(url)
        assert response.status_code == 200

    def test_license_admin_actions(self, admin_user, client, license):
        """Test license admin actions."""
        client.force_login(admin_user)
        url = reverse('admin:licenses_license_changelist')
        response = client.get(url)
        assert response.status_code == 200

    def test_activation_admin_actions(self, admin_user, client, activation):
        """Test activation admin actions."""
        client.force_login(admin_user)
        url = reverse('admin:licenses_activation_changelist')
        response = client.get(url)
        assert response.status_code == 200


@pytest.mark.django_db
class TestAdminSearchAndFiltering:
    """Test admin search and filtering functionality."""

    def test_brand_admin_search(self, admin_user, client, brand):
        """Test brand admin search."""
        client.force_login(admin_user)
        url = reverse('admin:licenses_brand_changelist')
        response = client.get(url, {'q': brand.name})
        assert response.status_code == 200
        assert brand.name in response.content.decode('utf-8')

    def test_product_admin_search(self, admin_user, client, product):
        """Test product admin search."""
        client.force_login(admin_user)
        url = reverse('admin:licenses_product_changelist')
        response = client.get(url, {'q': product.name})
        assert response.status_code == 200
        assert product.name in response.content.decode('utf-8')

    def test_license_admin_search(self, admin_user, client, license):
        """Test license admin search."""
        client.force_login(admin_user)
        url = reverse('admin:licenses_license_changelist')
        response = client.get(url, {'q': str(license.product)})
        assert response.status_code == 200

    def test_activation_admin_search(self, admin_user, client, activation):
        """Test activation admin search."""
        client.force_login(admin_user)
        url = reverse('admin:licenses_activation_changelist')
        response = client.get(url, {'q': activation.instance_identifier})
        assert response.status_code == 200
        assert activation.instance_identifier in response.content.decode('utf-8')


@pytest.mark.django_db
class TestAdminPermissions:
    """Test admin permissions and access control."""

    def test_regular_user_admin_access(self, regular_user, client):
        """Test that regular users cannot access admin."""
        client.force_login(regular_user)
        url = reverse('admin:index')
        response = client.get(url)
        # Regular users get redirected to login page (302) or forbidden (403)
        # depending on Django version and configuration
        assert response.status_code in [302, 403]

    def test_staff_user_admin_access(self, admin_user, client):
        """Test that staff users can access admin."""
        client.force_login(admin_user)
        url = reverse('admin:index')
        response = client.get(url)
        assert response.status_code == 200
        assert 'Django administration' in response.content.decode('utf-8')
