from django.contrib.admin import AdminSite
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import gettext_lazy


class CustomAdminSite(AdminSite):
    site_header = 'PLASU Examination System'
    site_title = 'PLASU Exam Admin'
    index_title = 'Welcome to PLASU Examination System Administration'
    
    def has_permission(self, request):
        """
        Return True if the given HttpRequest has permission to view *at least one* page in the admin site.
        """
        return request.user.is_active and request.user.is_staff


# Create a custom admin site
custom_admin_site = CustomAdminSite(name='custom_admin')

# Register the custom user with the custom admin site
from .models import User, UserProfile
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

@custom_admin_site.register(User)
class CustomUserAdmin(BaseUserAdmin):
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


@custom_admin_site.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'gender', 'date_of_birth')
    list_filter = ('gender',)
    search_fields = ('user__username', 'user__email')
