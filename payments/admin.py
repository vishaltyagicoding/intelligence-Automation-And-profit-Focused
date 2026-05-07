from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.utils.html import format_html
from .models import PaymentInfo

User = get_user_model()


class PaymentInfoAdmin(admin.ModelAdmin):
    """
    Admin interface for Payment Info
    Only accessible by alberttyagi123@gmail.com
    """
    list_display = ['user_name', 'subscription_price', 'payment_image_preview', 'created_at', 'created_by']
    list_filter = ['created_at']
    search_fields = ['user_name', 'user__email', 'user__username']
    readonly_fields = ['created_at', 'created_by', 'payment_image_preview']
    
    fieldsets = (
        ('Payment Information', {
            'fields': ('user', 'user_name', 'subscription_price')
        }),
        ('Payment Proof', {
            'fields': ('payment_valid_image', 'payment_image_preview')
        }),
        ('Metadata', {
            'fields': ('created_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )
    
    def payment_image_preview(self, obj):
        if obj.payment_valid_image:
            return format_html(
                '<img src="{}" style="max-width: 200px; max-height: 200px;" />',
                obj.payment_valid_image.url
            )
        return "No image"
    payment_image_preview.short_description = 'Payment Proof Preview'
    
    def has_module_permission(self, request):
        """Only alberttyagi123@gmail.com can see this module"""
        return request.user.is_superuser and request.user.email in ['alberttyagi123@gmail.com', 'pythonbyvishal@gmail.com']
    
    def has_view_permission(self, request, obj=None):
        """Only alberttyagi123@gmail.com can view"""
        return request.user.is_superuser and request.user.email in ['alberttyagi123@gmail.com', 'pythonbyvishal@gmail.com']
    
    def has_add_permission(self, request):
        """Only alberttyagi123@gmail.com can add"""
        return request.user.is_superuser and request.user.email in ['alberttyagi123@gmail.com', 'pythonbyvishal@gmail.com']
    
    def has_change_permission(self, request, obj=None):
        """Only alberttyagi123@gmail.com can change"""
        return request.user.is_superuser and request.user.email in ['alberttyagi123@gmail.com', 'pythonbyvishal@gmail.com']
    
    def has_delete_permission(self, request, obj=None):
        """Only alberttyagi123@gmail.com can delete"""
        return request.user.is_superuser and request.user.email in ['alberttyagi123@gmail.com', 'pythonbyvishal@gmail.com']
    
    def save_model(self, request, obj, form, change):
        """Set created_by to current superuser"""
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


# Register PaymentInfo model
admin.site.register(PaymentInfo, PaymentInfoAdmin)
