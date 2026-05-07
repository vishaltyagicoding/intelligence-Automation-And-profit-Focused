"""
URL configuration for trading app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'trades', views.TradeViewSet, basename='trade')
router.register(r'signals', views.MarketSignalViewSet, basename='signal')

urlpatterns = [
    path('', include(router.urls)),
    path('status/', views.system_status, name='system-status'),
    # Reversal Entry Zones API
    path('reversal-zones/', views.list_reversal_symbols, name='reversal-zones-list'),
    path('reversal-zones/<str:symbol>/', views.get_reversal_zones, name='reversal-zones-detail'),
    # Permanent signal history from database
    path('signal-history/<str:symbol>/', views.get_signal_history, name='signal-history'),
    # Trigger 30-day historical signal calculation
    path('calculate-history/<str:symbol>/', views.trigger_history_calculation, name='calculate-history'),
]