"""
Django signals for ReversalZone model.
Sends INSTANT email notifications when new signals are created.
"""
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import ReversalZone

logger = logging.getLogger(__name__)

# Track processed signals to avoid duplicate emails on update_or_create
_processed_signals = set()


@receiver(post_save, sender=ReversalZone)
def send_instant_email_on_new_signal(sender, instance, created, **kwargs):
    """
    Send email notification INSTANTLY when a new signal is created.
    
    This ensures users receive alerts at the EXACT moment the signal fires,
    not delayed by Celery periodic tasks.
    
    CRITICAL: Only sends on CREATE, not UPDATE (to avoid duplicate emails).
    Uses a fingerprint cache to prevent duplicates on rapid saves.
    """
    # Only send email for NEW signals (created=True)
    if not created:
        return
    
    # Create fingerprint to prevent duplicate emails
    fingerprint = f"{instance.symbol}:{instance.timeframe}:{instance.reversal_time.isoformat()}"
    
    if fingerprint in _processed_signals:
        logger.debug("Skipping duplicate email for %s", fingerprint)
        return
    
    # Mark as processed
    _processed_signals.add(fingerprint)
    
    # Clean up old fingerprints (keep last 1000)
    if len(_processed_signals) > 1000:
        _processed_signals.clear()
    
    try:
        from signal_alerts.email_utils import notify_signal_subscribers
        import pytz
        
        # Convert Binance format (BTCUSDT) → user-facing format (BTCUSD)
        BINANCE_TO_USER = {
            'BTCUSDT': 'BTCUSD',
            'ETHUSDT': 'ETHUSD',
            'LTCUSDT': 'LTCUSD',
            'PAXGUSDT': 'XAUUSD',
            'XAUUSDT': 'XAUUSD',
        }
        
        user_symbol = BINANCE_TO_USER.get(instance.symbol.upper(), instance.symbol)
        
        is_bull = instance.is_bullish
        entry = round(float(instance.center_price), 2)
        
        # Use the new stop_loss and target fields if available
        if instance.stop_loss and instance.target:
            stop_loss = round(float(instance.stop_loss), 2)
            target = round(float(instance.target), 2)
        else:
            # Fallback to outer_top/outer_bottom
            outer_top = round(float(instance.outer_top), 2)
            outer_bot = round(float(instance.outer_bottom), 2)
            stop_loss = outer_bot if is_bull else outer_top
            target = outer_top if is_bull else outer_bot
        
        # Format timestamp
        ts_str = instance.reversal_time.astimezone(pytz.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
        
        signal_data = {
            'crypto': user_symbol,
            'timeframe': instance.timeframe,
            'signal_type': 'BUY' if is_bull else 'SELL',
            'entry_price': entry,
            'target': target,
            'stop_loss': stop_loss,
            'timestamp': ts_str,
        }
        
        # Send email notifications to paid subscribers
        notifications_sent = notify_signal_subscribers(signal_data)
        
        if notifications_sent > 0:
            logger.info(
                "📧 INSTANT EMAIL: %d sent for %s %s %s @ %.2f (SL=%.2f, TP=%.2f)",
                notifications_sent, user_symbol, instance.timeframe,
                signal_data['signal_type'], entry, stop_loss, target
            )
        else:
            logger.debug(
                "No subscribers for %s %s %s",
                user_symbol, instance.timeframe, signal_data['signal_type']
            )
    
    except Exception as e:
        logger.error(
            "Error sending instant email for signal %s %s: %s",
            instance.symbol, instance.timeframe, e,
            exc_info=True
        )
