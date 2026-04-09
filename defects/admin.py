from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import Defect, Product,UserProfile

@admin.register(Defect)
class DefectAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'status', 'severity', 'priority', 'assigned_to', 'date_reported']
    list_filter = ['status', 'severity', 'priority']
    search_fields = ['title', 'description', 'tester_email']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['product_id', 'version', 'owner', 'description']
    filter_horizontal = ['developers']
    search_fields = ['product_id', 'version']
    list_filter = ['owner']

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'

class CustomUserAdmin(UserAdmin):
    inlines = [UserProfileInline]
    list_display = ['username', 'email', 'get_custom_user_id']

    def get_custom_user_id(self, obj):
        return obj.profile.custom_user_id if hasattr(obj, 'profile') else None
    get_custom_user_id.short_description = 'User ID'

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)