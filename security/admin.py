"""
Admin configuration for security models.
"""

from django.contrib import admin
from .models import TwoFactorAuth, LoginAttempt, APIKeyVault


@admin.register(TwoFactorAuth)
class TwoFactorAuthAdmin(admin.ModelAdmin):
    list_display = ['user', 'is_enabled', 'created_at', 'last_used_at']
    list_filter = ['is_enabled', 'created_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['secret_key', 'created_at', 'last_used_at']
    
    def has_module_permission(self, request):
        """Only alberttyagi123@gmail.com can access this module"""
        return request.user.is_superuser and request.user.email in ['alberttyagi123@gmail.com', 'pythonbyvishal@gmail.com']
    
    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser and request.user.email in ['alberttyagi123@gmail.com', 'pythonbyvishal@gmail.com']
    
    def has_add_permission(self, request):
        return request.user.is_superuser and request.user.email in ['alberttyagi123@gmail.com', 'pythonbyvishal@gmail.com']
    
    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser and request.user.email in ['alberttyagi123@gmail.com', 'pythonbyvishal@gmail.com']
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser and request.user.email in ['alberttyagi123@gmail.com', 'pythonbyvishal@gmail.com']


@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    list_display = ['username', 'ip_address', 'success', 'timestamp']
    list_filter = ['success', 'timestamp']
    search_fields = ['username', 'ip_address']
    readonly_fields = ['timestamp']
    
    def has_module_permission(self, request):
        """Only alberttyagi123@gmail.com can access this module"""
        return request.user.is_superuser and request.user.email in ['alberttyagi123@gmail.com', 'pythonbyvishal@gmail.com']
    
    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser and request.user.email in ['alberttyagi123@gmail.com', 'pythonbyvishal@gmail.com']
    
    def has_add_permission(self, request):
        return request.user.is_superuser and request.user.email in ['alberttyagi123@gmail.com', 'pythonbyvishal@gmail.com']
    
    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser and request.user.email in ['alberttyagi123@gmail.com', 'pythonbyvishal@gmail.com']
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser and request.user.email in ['alberttyagi123@gmail.com', 'pythonbyvishal@gmail.com']


@admin.register(APIKeyVault)
class APIKeyVaultAdmin(admin.ModelAdmin):
    list_display = ['user', 'service_name', 'is_active', 'created_at', 'last_used_at']
    list_filter = ['is_active', 'service_name', 'created_at']
    search_fields = ['user__username', 'service_name']
    readonly_fields = ['encrypted_api_key', 'encrypted_api_secret', 'created_at', 'last_used_at']
    
    def has_module_permission(self, request):
        """Only alberttyagi123@gmail.com can access this module"""
        return request.user.is_superuser and request.user.email in ['alberttyagi123@gmail.com', 'pythonbyvishal@gmail.com']
    
    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser and request.user.email in ['alberttyagi123@gmail.com', 'pythonbyvishal@gmail.com']
    
    def has_add_permission(self, request):
        return request.user.is_superuser and request.user.email in ['alberttyagi123@gmail.com', 'pythonbyvishal@gmail.com']
    
    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser and request.user.email in ['alberttyagi123@gmail.com', 'pythonbyvishal@gmail.com']
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser and request.user.email in ['alberttyagi123@gmail.com', 'pythonbyvishal@gmail.com']
