from django.contrib import admin
from .models import SignalAlert


@admin.register(SignalAlert)
class SignalAlertAdmin(admin.ModelAdmin):
    list_display = ['user', 'crypto', 'timeframe', 'email', 'is_active', 'created_at']
    list_filter = ['crypto', 'timeframe', 'is_active', 'created_at']
    search_fields = ['user__username', 'user__email', 'email']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Alert Information', {
            'fields': ('user', 'crypto', 'timeframe', 'email')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
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
