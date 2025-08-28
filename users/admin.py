from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Admin interface for the custom User model.
    Provides a clean, professional interface for managing users.
    """
    
    list_display = (
        'username', 
        'email', 
        'first_name', 
        'last_name', 
        'company_name',
        'is_license_admin',
        'is_active', 
        'date_joined'
    )
    
    list_filter = (
        'is_license_admin',
        'is_active', 
        'is_staff', 
        'is_superuser',
        'date_joined',
        'company_name'
    )
    
    search_fields = (
        'username', 
        'first_name', 
        'last_name', 
        'email', 
        'company_name'
    )
    
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {
            'fields': (
                'first_name', 
                'last_name', 
                'email', 
                'company_name',
                'phone_number',
                'address'
            )
        }),
        (_('Permissions'), {
            'fields': (
                'is_active',
                'is_staff', 
                'is_superuser',
                'is_license_admin',
                'groups',
                'user_permissions',
            ),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username', 
                'email', 
                'password1', 
                'password2',
                'first_name',
                'last_name',
                'company_name'
            ),
        }),
    )
    
    readonly_fields = ('date_joined', 'last_login')
    
    def get_queryset(self, request):
        """Optimize queryset for admin display."""
        return super().get_queryset(request).select_related()
