"""
Signal Alert Email Tasks
=========================
Celery tasks for sending signal alert emails reliably.

WHY THIS EXISTS (root cause of the email delay bug):
  The previous implementation sent emails in a daemon Thread inside the
  Celery worker process. This caused 1-4 hour delays because:

  1. The Celery worker (prefork, concurrency=4) had 31,000+ tasks backed up
     in the queue. All 4 worker slots were permanently busy processing
     update_recent_signals_for_symbol_timeframe tasks.

  2. daemon=True Thread started inside a CPU-bound worker process gets
     starved of OS scheduling time. The SMTP connection (smtp.gmail.com:587,
     timeout=30s) was delayed by minutes or hours waiting for CPU time.

  3. Gmail SMTP may rate-limit burst sends → SMTP 421/450 → 5s sleep retry
     → further delay stacking up.

THE FIX:
  Email sending is now a proper Celery task on a dedicated 'emails' queue.
  The worker listens to: celery, status_updates, emails
  The 'emails' queue is isolated — it never competes with signal processing.
  Each email task runs as a first-class Celery job with full retry support.

  reversal_zones/signals.py now calls:
      send_signal_alert_task.apply_async(args=[signal_data], queue='emails')
  instead of:
      Thread(target=_send_emails, daemon=True).start()
"""
import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=30,   # 30 seconds between retries
    queue='emails',
    time_limit=120,           # 2 min hard limit per email batch
    soft_time_limit=90,
)
def send_signal_alert_task(self, signal_data: dict):
    """
    Send signal alert emails to all matching subscribers.

    This task runs on the dedicated 'emails' queue which is never blocked
    by the high-volume signal processing tasks on the 'celery' queue.

    Retries up to 3 times with 30-second delays on transient failures
    (SMTP errors, Redis timeouts, DB unavailability).

    Args:
        signal_data (dict): Signal information — same format as
            notify_signal_subscribers() expects:
            {
                'crypto':       'BTCUSD',
                'timeframe':    '5m',
                'signal_type':  'BUY' | 'SELL',
                'entry_price':  float,
                'stop_loss':    float,
                'target':       float,
                'timestamp':    'YYYY-MM-DD HH:MM:SS UTC',
                'timestamp_dt': datetime (UTC-aware),
            }
    """
    try:
        from signal_alerts.email_utils import notify_signal_subscribers

        crypto    = signal_data.get('crypto', 'N/A')
        timeframe = signal_data.get('timeframe', 'N/A')
        sig_type  = signal_data.get('signal_type', 'N/A')

        logger.info(
            "📧 send_signal_alert_task: sending emails for %s %s %s",
            crypto, timeframe, sig_type,
        )

        sent, failed = notify_signal_subscribers(signal_data)

        logger.info(
            "📊 send_signal_alert_task complete: %s %s %s — sent=%d failed=%d",
            crypto, timeframe, sig_type, sent, failed,
        )

        return {'status': 'ok', 'sent': sent, 'failed': failed}

    except Exception as exc:
        logger.error(
            "❌ send_signal_alert_task failed for %s %s: %s",
            signal_data.get('crypto', '?'),
            signal_data.get('timeframe', '?'),
            exc,
            exc_info=True,
        )
        # Retry on any exception (SMTP failures, DB issues, etc.)
        try:
            raise self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            logger.error(
                "❌ Max retries exceeded for signal alert email: %s %s %s",
                signal_data.get('crypto'),
                signal_data.get('timeframe'),
                signal_data.get('signal_type'),
            )
            return {'status': 'error', 'error': str(exc)}