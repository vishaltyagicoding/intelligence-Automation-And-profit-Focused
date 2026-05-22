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


def signal_health_check(request):
    """
    Deep health check for the signal delivery system.
    Returns the age of the last signal task heartbeat.

    GREEN  → task ran within last 3 minutes (normal)
    YELLOW → task ran 3–10 minutes ago (beat may be slow)
    RED    → task older than 10 minutes (beat is broken — action needed)

    Monitor this endpoint from an uptime service (UptimeRobot, BetterUptime etc.)
    to get alerted the moment the signal system stops working.
    """
    import time as _time
    import redis as _redis
    from django.conf import settings as _settings

    result = {
        'signal_system': 'unknown',
        'last_task_run': None,
        'age_seconds': None,
        'scheduler': 'celery.beat:PersistentScheduler',
        'expected_interval_seconds': 60,
        'timestamp': timezone.now().isoformat(),
    }

    try:
        r = _redis.Redis(
            host=getattr(_settings, 'REDIS_HOST', 'redis'),
            port=getattr(_settings, 'REDIS_PORT', 6379),
            db=4,
            socket_connect_timeout=2,
            decode_responses=True,
        )
        heartbeat = r.get('beat:heartbeat:update_all_recent_signals')
        if heartbeat:
            last_run_ts = int(heartbeat)
            age = int(_time.time()) - last_run_ts
            result['age_seconds'] = age
            result['last_task_run'] = timezone.datetime.fromtimestamp(
                last_run_ts, tz=timezone.utc
            ).isoformat()
            if age < 180:
                result['signal_system'] = 'healthy'
            elif age < 600:
                result['signal_system'] = 'degraded'
            else:
                result['signal_system'] = 'dead'
        else:
            result['signal_system'] = 'no_heartbeat_yet'
            result['note'] = 'Task has not run yet since last deploy — normal on first boot'
    except Exception as e:
        result['signal_system'] = 'redis_error'
        result['error'] = str(e)

    status_code = 200 if result['signal_system'] in ('healthy', 'no_heartbeat_yet') else 503
    return JsonResponse(result, status=status_code)


urlpatterns = [
    path('health/', health_check, name='health-check'),              # Docker health check
    path('health/signals/', signal_health_check, name='signal-health'),  # Signal system monitor
    path('admin/', admin.site.urls),
    path('', include('landing.urls')),  # Landing page at /join
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