"""
URL configuration for NeuralTrade project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from django.utils import timezone


def health_check(request):
    """Simple health check endpoint for Docker"""
    return JsonResponse({
        'status': 'healthy',
        'timestamp': timezone.now().isoformat()
    })


urlpatterns = [
    path('health/', health_check, name='health-check'),  # Docker health check
    path('admin/', admin.site.urls),
    path('', include('api_docs.urls')),  # API Documentation Homepage
    path('api/trading/', include('trading.urls')),
    path('api/users/', include('users.urls')),
    path('api/payments/', include('payments.urls')),
    path('api/market/', include('market_data.urls')),
    path('api/auth/', include('security.urls')),
    path('api/signal-alerts/', include('signal_alerts.urls')),  # Signal Alerts
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
