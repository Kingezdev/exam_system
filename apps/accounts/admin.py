from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User as DjangoUser
from django.contrib.admin.sites import AdminSite
from django.urls import path
from django.shortcuts import redirect
from .models import User, UserProfile


class CustomAdminSite(AdminSite):
    def get_urls(self):
        urls = super().get_urls()
        # Add a custom URL to handle auth/user redirect
        custom_urls = [
            path('auth/user/', self.admin_view(self.redirect_to_custom_user), name='auth_user_changelist'),
        ]
        return custom_urls + urls
    
    def redirect_to_custom_user(self, request):
        """Redirect auth/user/ to accounts/user/"""
        return redirect('admin:accounts_user_changelist')


# Replace the default admin site with our custom one
admin.site.__class__ = CustomAdminSite

# Unregister the default Django User model if it's registered
try:
    admin.site.unregister(DjangoUser)
except admin.sites.NotRegistered:
    pass


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Information', {
            'fields': ('role', 'phone_number', 'staff_id', 'student_id', 'department')
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Additional Information', {
            'fields': ('email', 'role', 'phone_number')
        }),
    )


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'gender', 'date_of_birth')
    list_filter = ('gender',)
    search_fields = ('user__username', 'user__email')
