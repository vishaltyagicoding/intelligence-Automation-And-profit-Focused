"""
URL configuration for market data app.
"""

from django.urls import path
from . import views

urlpatterns = [
    path('data/', views.get_market_data, name='market-data'),
    path('historical/', views.get_historical_data, name='historical-data'),
    path('ohlcv/<str:symbol>/', views.get_ohlcv, name='ohlcv'),
]
