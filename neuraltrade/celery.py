"""
Celery configuration for NeuralTrade.
"""

import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'neuraltrade.settings')

app = Celery('neuraltrade')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# ── Queue routing ──────────────────────────────────────────────────────────────
# Each queue is isolated so high-volume tasks never starve critical ones.
#
# 'celery'        — default queue for signal processing (high volume)
# 'status_updates'— check_signal_statuses (runs every 2 min, must never be buried)
# 'emails'        — signal alert email delivery (must be near-instant, highest priority)
#
# ROOT CAUSE FIX: emails were previously sent via daemon Thread inside heavily
# loaded prefork workers, causing 1-4 hour delays from CPU starvation.
# Moving to a dedicated 'emails' queue gives emails their own processing lane.
app.conf.task_routes = {
    'reversal_zones.tasks.check_signal_statuses':    {'queue': 'status_updates'},
    'signal_alerts.tasks.send_signal_alert_task':    {'queue': 'emails'},
}
app.conf.task_default_queue = 'celery'

# Celery Beat Schedule
app.conf.beat_schedule = {
    'auto-login-shoonya': {
        'task': 'trading.tasks.auto_login_shoonya',
        'schedule': crontab(hour=8, minute=45),  # 8:45 AM daily
    },
    'refresh-binance-token': {
        'task': 'trading.tasks.refresh_binance_token',
        'schedule': crontab(hour='*/6'),  # Every 6 hours
    },
    'market-watch-heartbeat': {
        'task': 'trading.tasks.market_watch_heartbeat',
        'schedule': 1.0,  # Every 1 second
    },
    'cleanup-expired-tokens': {
        'task': 'trading.tasks.cleanup_expired_tokens',
        'schedule': crontab(hour=0, minute=0),  # Midnight daily
    },
    'calculate-signal-history': {
        'task': 'reversal_zones.tasks.calculate_all_history',
        'schedule': crontab(hour=0, minute=30),  # 12:30 AM daily - add new signals to history
    },
    'check-expired-subscriptions': {
        'task': 'users.tasks.check_and_expire_subscriptions',
        'schedule': 60.0,  # Every 1 minute - check and expire subscriptions at exact time
    },
    'check-signal-statuses': {
        'task': 'reversal_zones.tasks.check_signal_statuses',
        'schedule': 300.0,  # Backup every 5 min — self-scheduling handles 2-min cadence.
        'options': {'queue': 'status_updates'},  # dedicated queue, never buried
    },
}

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')