"""
Admin configuration for trading models.
"""

from django.contrib import admin
from .models import Trade, TradingSession, MarketSignal


@admin.register(Trade)
class TradeAdmin(admin.ModelAdmin):
    list_display = ['order_id', 'user', 'symbol', 'trade_type', 'status', 'pnl', 'created_at']
    list_filter = ['status', 'market', 'trade_type', 'created_at']
    search_fields = ['order_id', 'symbol', 'user__username']
    readonly_fields = ['created_at', 'executed_at', 'closed_at']
    
    def has_module_permission(self, request):
        """Only alberttyagi123@gmail.com can access this module"""
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


@admin.register(TradingSession)
class TradingSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'date', 'trades_count', 'total_pnl', 'win_rate', 'is_active']
    list_filter = ['date', 'is_active']
    search_fields = ['user__username']
    
    def has_module_permission(self, request):
        """Only alberttyagi123@gmail.com can access this module"""
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


@admin.register(MarketSignal)
class MarketSignalAdmin(admin.ModelAdmin):
    list_display = ['symbol', 'action', 'confidence', 'created_at', 'is_executed']
    list_filter = ['action', 'market', 'is_executed', 'created_at']
    search_fields = ['symbol']
    
    def has_module_permission(self, request):
        """Only alberttyagi123@gmail.com can access this module"""
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
