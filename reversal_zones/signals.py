"""
Django signals for ReversalZone model.
Sends INSTANT email notifications when new signals are created.
"""
import logging
from datetime import datetime, timedelta

import pytz
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import ReversalZone

logger = logging.getLogger(__name__)


# ── Redis-based dedup (survives Django restarts, Docker restarts, deploys) ────
# In-memory sets clear on restart → old signals get re-emailed.
# Redis with 7-day TTL is the only reliable solution.

def _redis_client():
    """Get a Redis client for email dedup. Uses DB=3 (dedicated)."""
    import redis as _redis_lib
    from django.conf import settings
    return _redis_lib.Redis(
        host=getattr(settings, 'REDIS_HOST', 'redis'),
        port=getattr(settings, 'REDIS_PORT', 6379),
        db=3,
        socket_connect_timeout=2,
        socket_timeout=2,
        decode_responses=True,
    )


def _is_email_already_sent(fingerprint: str) -> bool:
    """Check if email was already sent for this signal fingerprint."""
    try:
        return bool(_redis_client().get(f"email:sent:{fingerprint}"))
    except Exception as e:
        logger.warning("Redis dedup check failed (will send): %s", e)
        return False  # fail OPEN — better to send a duplicate than miss an alert


def _mark_email_sent(fingerprint: str) -> None:
    """Mark signal email as sent in Redis. TTL = 7 days."""
    try:
        _redis_client().set(f"email:sent:{fingerprint}", "1", ex=7 * 24 * 3600)
    except Exception as e:
        logger.warning("Redis dedup mark failed: %s", e)


# ─────────────────────────────────────────────────────────────────────────────

@receiver(post_save, sender=ReversalZone)
def send_instant_email_on_new_signal(sender, instance, created, **kwargs):
    """
    Send email INSTANTLY when a new ReversalZone signal is created.

    Rules:
    1. Only fires on CREATE (not UPDATE) — no duplicate emails on data refresh.
    2. Redis dedup: if email was already sent for this fingerprint (same symbol +
       timeframe + reversal_time), skip — survives restarts and redeploys.
    3. Freshness guard: skip if signal is older than 30 minutes — prevents old
       signals from being emailed when DB is repopulated after a wipe/deploy.
    4. Runs in background Thread so post_save returns instantly (no SMTP blocking).
    """
    if not created:
        return

    # ── Build fingerprint ────────────────────────────────────────────────────
    try:
        fingerprint = (
            f"{instance.symbol}:{instance.timeframe}:"
            f"{instance.reversal_time.isoformat()}"
        )
    except Exception:
        return

    # ── GUARD 1: Redis dedup ─────────────────────────────────────────────────
    if _is_email_already_sent(fingerprint):
        logger.debug("⏭️ Email already sent (Redis dedup): %s", fingerprint)
        return

    # ── GUARD 2: Freshness check — 30-min hard cutoff ────────────────────────
    try:
        utc_dt = instance.reversal_time.astimezone(pytz.utc)
    except Exception:
        utc_dt = None

    if utc_dt is not None:
        age = datetime.now(pytz.utc) - utc_dt
        if age > timedelta(minutes=30):
            logger.debug(
                "⏭️ Skipping stale signal email (%s old): %s",
                str(age).split('.')[0], fingerprint
            )
            # Still mark as sent so this old signal is never emailed later either
            _mark_email_sent(fingerprint)
            return

    # ── Mark sent in Redis BEFORE spawning thread (prevents race on rapid saves) ──
    _mark_email_sent(fingerprint)

    # ── Build signal_data ────────────────────────────────────────────────────
    try:
        from signal_alerts.email_utils import notify_signal_subscribers

        BINANCE_TO_USER = {
            'BTCUSDT':  'BTCUSD',
            'ETHUSDT':  'ETHUSD',
            'LTCUSDT':  'LTCUSD',
            'PAXGUSDT': 'XAUUSD',
            'XAUUSDT':  'XAUUSD',
        }
        user_symbol = BINANCE_TO_USER.get(instance.symbol.upper(), instance.symbol)
        is_bull     = instance.is_bullish
        entry       = round(float(instance.center_price), 2)

        if instance.stop_loss and instance.target:
            stop_loss = round(float(instance.stop_loss), 2)
            target    = round(float(instance.target),    2)
        else:
            outer_top = round(float(instance.outer_top),    2)
            outer_bot = round(float(instance.outer_bottom), 2)
            stop_loss = outer_bot if is_bull else outer_top
            target    = outer_top if is_bull else outer_bot

        ts_utc = utc_dt.strftime('%Y-%m-%d %H:%M:%S UTC') if utc_dt else ''

        signal_data = {
            'crypto':       user_symbol,
            'timeframe':    instance.timeframe,
            'signal_type':  'BUY' if is_bull else 'SELL',
            'entry_price':  entry,
            'target':       target,
            'stop_loss':    stop_loss,
            'timestamp':    ts_utc,    # UTC fallback string
            'timestamp_dt': utc_dt,    # raw datetime — per-user tz conversion
        }
    except Exception as e:
        logger.error("Error building signal_data for %s: %s", fingerprint, e, exc_info=True)
        return

    # ── Send emails in background Thread (non-blocking) ─────────────────────
    from threading import Thread

    def _send_emails():
        try:
            sent = notify_signal_subscribers(signal_data)
            if sent > 0:
                logger.info(
                    "📧 INSTANT EMAIL: %d sent for %s %s %s @ %.2f (SL=%.2f, TP=%.2f)",
                    sent, user_symbol, instance.timeframe,
                    signal_data['signal_type'], entry, stop_loss, target,
                )
            else:
                logger.debug(
                    "No active subscribers for %s %s %s",
                    user_symbol, instance.timeframe, signal_data['signal_type'],
                )
        except Exception as exc:
            logger.error(
                "Error sending instant email [%s]: %s", fingerprint, exc, exc_info=True
            )

    Thread(target=_send_emails, daemon=True).start()
    logger.info(
        "🔔 Signal email dispatched (background): %s %s %s @ %.2f",
        user_symbol, instance.timeframe,
        signal_data['signal_type'], entry,
    )