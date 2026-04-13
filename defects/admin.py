from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import Defect, Product,UserProfile

@admin.register(Defect)
class DefectAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'status', 'severity', 'priority', 'assigned_to', 'date_reported']
    list_filter = ['status', 'severity', 'priority']
    search_fields = ['title', 'description', 'tester_email']
    
    def save_model(self, request, obj, form, change):
        if obj.product:
            obj.version = obj.product.version
        super().save_model(request, obj, form, change)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['product_id', 'version', 'owner', 'expiry_date', 'description']
    list_filter = ['owner', 'expiry_date']
    search_fields = ['product_id', 'version']
    filter_horizontal = ['developers']
    fields = ['product_id', 'version', 'owner', 'developers', 'expiry_date', 'description']


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