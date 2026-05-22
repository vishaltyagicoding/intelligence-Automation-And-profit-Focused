"""
Django signals for ReversalZone model.
Sends INSTANT email notifications when new signals are created.
"""
import logging
from datetime import datetime, timedelta
from threading import Thread

import pytz
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import ReversalZone

logger = logging.getLogger(__name__)

# Symbol mapping: Binance format → user-facing format
BINANCE_TO_USER = {
    'BTCUSDT':  'BTCUSD',
    'ETHUSDT':  'ETHUSD',
    'LTCUSDT':  'LTCUSD',
    'PAXGUSDT': 'XAUUSD',
    'XAUUSDT':  'XAUUSD',
}


# ── Redis dedup client (DB=3) ─────────────────────────────────────────────────

def _redis_client():
    """Dedicated Redis client (DB=3) for email dedup — 7-day TTL per signal."""
    import redis as _r
    from django.conf import settings
    return _r.Redis(
        host=getattr(settings, 'REDIS_HOST', 'redis'),
        port=getattr(settings, 'REDIS_PORT', 6379),
        db=3,
        socket_connect_timeout=2,
        socket_timeout=2,
        decode_responses=True,
    )


def _is_email_already_sent(fingerprint: str) -> bool:
    try:
        return bool(_redis_client().get(f"email:sent:{fingerprint}"))
    except Exception as e:
        # Redis down → fail OPEN (send the email — duplicate is better than silence)
        logger.warning("Redis dedup read failed (will send email): %s", e)
        return False


def _mark_email_sent(fingerprint: str) -> None:
    try:
        _redis_client().set(f"email:sent:{fingerprint}", "1", ex=7 * 24 * 3600)
    except Exception as e:
        logger.warning("Redis dedup write failed: %s", e)


# ─────────────────────────────────────────────────────────────────────────────

@receiver(post_save, sender=ReversalZone)
def send_instant_email_on_new_signal(sender, instance, created, **kwargs):
    """
    Send email INSTANTLY when a NEW ReversalZone signal is created.

    KEY DESIGN DECISIONS (fixes for previous bugs):

    1. Only fires on CREATE (not UPDATE). Django's `created=True` flag is the
       primary dedup guard — it means this DB row was just inserted now.

    2. Freshness is checked using `instance.created_at` (when the DB row was
       saved), NOT `instance.reversal_time` (when the candle closed).
       This is critical: a 4H candle that closed at 08:00 and gets detected
       at 08:35 has reversal_time=08:00 but created_at=08:35.
       Using reversal_time with a 30-min cutoff would BLOCK IT — this was
       the bug causing emails to stop being sent entirely.

    3. Redis dedup uses the fingerprint as a safety net against the rare case
       where the same DB row is somehow created twice. TTL = 7 days.

    4. Redis is marked as sent AFTER email succeeds (not before).
       Marking before meant a failed email would permanently silence that signal.

    5. Email runs in a background Thread — post_save returns instantly.
    """
    if not created:
        return

    # ── Build fingerprint ─────────────────────────────────────────────────────
    try:
        fingerprint = (
            f"{instance.symbol}:{instance.timeframe}:"
            f"{instance.reversal_time.isoformat()}"
        )
    except Exception as e:
        logger.error("Cannot build fingerprint for signal %s: %s", instance.pk, e)
        return

    # ── GUARD: Redis dedup ────────────────────────────────────────────────────
    if _is_email_already_sent(fingerprint):
        logger.debug("⏭️  Dedup skip (already sent): %s", fingerprint)
        return

    # ── FRESHNESS CHECK using created_at (DB save time), NOT reversal_time ───
    # reversal_time = candle close timestamp (can be hours old for higher TFs)
    # created_at    = when this row was inserted into DB (always ~now)
    try:
        created_at_utc = instance.created_at.astimezone(pytz.utc)
        age_at_save = datetime.now(pytz.utc) - created_at_utc
        if age_at_save > timedelta(minutes=10):
            # Signal DB row itself is more than 10 min old — likely from a
            # backfill / migration / calculate_all_history run, not a live signal.
            # Skip to avoid emailing old historical data.
            logger.info(
                "⏭️  Skipping old DB row (created %s ago): %s",
                str(age_at_save).split('.')[0], fingerprint
            )
            _mark_email_sent(fingerprint)  # prevent future re-attempts
            return
    except Exception:
        pass  # created_at missing or malformed — proceed with send

    # ── Get UTC datetime of reversal for email timestamp display ─────────────
    try:
        utc_dt = instance.reversal_time.astimezone(pytz.utc)
    except Exception:
        utc_dt = None

    # ── Build signal_data ─────────────────────────────────────────────────────
    try:
        from signal_alerts.email_utils import notify_signal_subscribers

        user_symbol = BINANCE_TO_USER.get(instance.symbol.upper(), instance.symbol)
        is_bull     = instance.is_bullish
        entry       = round(float(instance.center_price), 2)

        if instance.stop_loss and instance.target:
            stop_loss = round(float(instance.stop_loss), 2)
            target    = round(float(instance.target), 2)
        else:
            outer_top = round(float(instance.outer_top), 2)
            outer_bot = round(float(instance.outer_bottom), 2)
            stop_loss = outer_bot if is_bull else outer_top
            target    = outer_top if is_bull else outer_bot

        ts_utc_str = utc_dt.strftime('%Y-%m-%d %H:%M:%S UTC') if utc_dt else ''

        signal_data = {
            'crypto':       user_symbol,
            'timeframe':    instance.timeframe,
            'signal_type':  'BUY' if is_bull else 'SELL',
            'entry_price':  entry,
            'target':       target,
            'stop_loss':    stop_loss,
            'timestamp':    ts_utc_str,   # UTC fallback string for display
            'timestamp_dt': utc_dt,       # raw datetime for per-user tz conversion
        }
    except Exception as e:
        logger.error(
            "Error building signal_data for %s: %s", fingerprint, e, exc_info=True
        )
        return

    # ── Send emails in background Thread (non-blocking post_save) ────────────
    # Redis is marked AFTER successful send to ensure no signal is silently dropped.

    def _send_emails():
        try:
            sent = notify_signal_subscribers(signal_data)
            # Mark sent in Redis ONLY after successful send
            _mark_email_sent(fingerprint)
            if sent > 0:
                logger.info(
                    "✅ EMAIL SENT: %d alert(s) for %s %s %s @ %.2f (SL=%.2f TP=%.2f)",
                    sent, user_symbol, instance.timeframe,
                    signal_data['signal_type'], entry, stop_loss, target,
                )
            else:
                logger.info(
                    "ℹ️  No subscribers for %s %s %s — no emails sent",
                    user_symbol, instance.timeframe, signal_data['signal_type'],
                )
                # Still mark sent so we don't retry for same signal
                _mark_email_sent(fingerprint)
        except Exception as exc:
            # Do NOT mark Redis on exception — allow retry on next task run
            logger.error(
                "❌ Email send FAILED [%s]: %s", fingerprint, exc, exc_info=True
            )

    Thread(target=_send_emails, daemon=True).start()
    logger.info(
        "🔔 Email thread started: %s %s %s @ %.2f",
        user_symbol, instance.timeframe, signal_data['signal_type'], entry,
    )


# ── One-time Redis flush helper (run from Django shell after deploy) ──────────
def flush_email_dedup_cache():
    """
    Call this after deploying to clear any wrongly-blocked signal fingerprints
    that were set during the broken period (when emails were not being sent).

    Run from server:
        docker-compose exec django python manage.py shell -c "
        from reversal_zones.signals import flush_email_dedup_cache
        flush_email_dedup_cache()
        "
    """
    try:
        r = _redis_client()
        keys = r.keys("email:sent:*")
        if keys:
            r.delete(*keys)
            logger.info("🧹 Flushed %d stale email dedup keys from Redis DB=3", len(keys))
        else:
            logger.info("🧹 No email dedup keys to flush")
        return len(keys)
    except Exception as e:
        logger.error("Failed to flush email dedup cache: %s", e)
        return 0