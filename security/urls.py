"""
URL configuration for security/auth.
"""

from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views

urlpatterns = [
    # JWT Authentication
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # 2FA
    path('2fa/setup/', views.setup_2fa, name='setup-2fa'),
    path('2fa/verify/', views.verify_2fa, name='verify-2fa'),
    path('2fa/disable/', views.disable_2fa, name='disable-2fa'),
]
