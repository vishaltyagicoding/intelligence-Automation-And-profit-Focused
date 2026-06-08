"""
Email Utility for Signal Alerts
================================
Sends email notifications when new trading signals are generated.

BUG FIXES IN THIS VERSION:
  FIX #2: failed deliveries now logged as WARNING per user, not silently dropped
  FIX #3: full diagnostic log before query (subscriber count, filter params)
  FIX #4: removed double-normalization — crypto is already normalized by signals.py
  FIX #5: SMTP retry (up to 2 attempts) on transient errors
  FIX #7: fallback to user.email if alert.email is empty/invalid
  FIX #8: use crypto_display name in email subject/body ("Gold (XAUUSD)" not "XAUUSD")
"""
import smtplib
import logging
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from django.conf import settings

logger = logging.getLogger(__name__)

# User-facing display names for email body
CRYPTO_DISPLAY_NAMES = {
    'BTCUSD':  'Bitcoin (BTCUSD)',
    'ETHUSD':  'Ethereum (ETHUSD)',
    'LTCUSD':  'Litecoin (LTCUSD)',
    'XAUUSD':  'Gold (XAUUSD)',
}

# Timeframe display labels
TIMEFRAME_LABELS = {
    '5m':  '5 Minutes',
    '15m': '15 Minutes',
    '30m': '30 Minutes',
    '1h':  '1 Hour',
    '2h':  '2 Hours',
    '4h':  '4 Hours',
    '1d':  '1 Day',
}


def send_signal_alert_email(email, username, signal_data, user_tz='UTC'):
    """
    Send signal alert email to a single user when a new signal is generated.

    Args:
        email (str): Recipient email address
        username (str): User's username for greeting
        signal_data (dict): Signal information containing:
            - crypto: User-facing symbol (ETHUSD, XAUUSD, etc.) — already normalized
            - crypto_display: Display name e.g. "Gold (XAUUSD)" — used in email body
            - timeframe: Timeframe string e.g. "1h"
            - signal_type: "BUY" or "SELL"
            - entry_price: Entry price (float)
            - stop_loss: Stop loss level (float)
            - target: Target level (float)
            - timestamp: Signal time (UTC string, fallback display)
            - timestamp_dt: Raw UTC datetime object (preferred for tz conversion)
        user_tz (str): IANA timezone name for the recipient (e.g. 'Asia/Kolkata')

    Returns:
        bool: True if email sent successfully, False otherwise

    FIX #5: SMTP is retried once on transient failure (421, 454, connection reset).
    """
    SMTP_MAX_RETRIES = 2

    for attempt in range(1, SMTP_MAX_RETRIES + 1):
        try:
            import pytz

            # Email configuration
            smtp_server    = "smtp.gmail.com"
            smtp_port      = 587
            sender_email   = settings.EMAIL_HOST_USER
            sender_password = settings.EMAIL_HOST_PASSWORD

            # FIX #8: Use display name ("Gold (XAUUSD)") instead of raw symbol ("XAUUSD")
            crypto         = signal_data.get('crypto', 'N/A')
            crypto_display = signal_data.get('crypto_display') or CRYPTO_DISPLAY_NAMES.get(crypto, crypto)
            timeframe_raw  = signal_data.get('timeframe', 'N/A')
            timeframe_label = TIMEFRAME_LABELS.get(timeframe_raw, timeframe_raw.upper())
            signal_type    = signal_data.get('signal_type', 'N/A')

            # ── Timezone-aware timestamp ──────────────────────────────────────
            raw_dt = signal_data.get('timestamp_dt')
            try:
                tz = pytz.timezone(user_tz)
            except Exception:
                tz = pytz.utc

            if raw_dt is not None:
                local_dt  = raw_dt.astimezone(tz)
                tz_label  = local_dt.strftime('%Z')
                timestamp = local_dt.strftime(f'%Y-%m-%d %H:%M:%S {tz_label}')
            else:
                timestamp = signal_data.get('timestamp', 'N/A')

            # ── Price formatting ──────────────────────────────────────────────
            def _fmt(val):
                try:
                    return f"{float(val):.2f}"
                except (TypeError, ValueError):
                    return 'N/A'

            entry_price = _fmt(signal_data.get('entry_price'))
            target      = _fmt(signal_data.get('target'))
            raw_stop    = signal_data.get('stop_loss')
            stop_loss   = _fmt(raw_stop) if raw_stop not in (None, '', 0, 'N/A') else 'N/A'

            # ── Signal styling ────────────────────────────────────────────────
            if signal_type == 'BUY':
                signal_color = '#10b981'
                signal_emoji = '📈'
                signal_bg    = 'rgba(16, 185, 129, 0.1)'
            else:
                signal_color = '#ef4444'
                signal_emoji = '📉'
                signal_bg    = 'rgba(239, 68, 68, 0.1)'

            # ── Compose message ───────────────────────────────────────────────
            message              = MIMEMultipart("alternative")
            message["Subject"]   = f"🔔 New {signal_type} Signal: {crypto_display} ({timeframe_label})"
            message["From"]      = f"SmartRisk Alerts <{sender_email}>"
            message["To"]        = email

            html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .container {{
                    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
                    border-radius: 10px;
                    padding: 30px;
                    color: #fff;
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 30px;
                }}
                .logo {{
                    font-size: 32px;
                    font-weight: bold;
                    color: #06b6d4;
                    margin-bottom: 10px;
                }}
                .signal-box {{
                    background: {signal_bg};
                    border: 2px solid {signal_color};
                    border-radius: 12px;
                    padding: 25px;
                    text-align: center;
                    margin: 30px 0;
                }}
                .signal-type {{
                    font-size: 48px;
                    font-weight: bold;
                    color: {signal_color};
                    margin: 10px 0;
                }}
                .crypto-info {{
                    font-size: 24px;
                    font-weight: bold;
                    color: #fff;
                    margin: 10px 0;
                }}
                .timeframe {{
                    font-size: 16px;
                    color: #94a3b8;
                    text-transform: uppercase;
                }}
                .details-grid {{
                    display: grid;
                    grid-template-columns: 1fr 1fr 1fr;
                    gap: 15px;
                    margin: 25px 0;
                }}
                .detail-box {{
                    background: rgba(59, 130, 246, 0.1);
                    border-left: 4px solid #3b82f6;
                    padding: 15px;
                    border-radius: 4px;
                }}
                .detail-box.stop-loss {{
                    background: rgba(239, 68, 68, 0.1);
                    border-left: 4px solid #ef4444;
                }}
                .detail-label {{
                    font-size: 12px;
                    color: #94a3b8;
                    text-transform: uppercase;
                    margin-bottom: 5px;
                }}
                .detail-value {{
                    font-size: 20px;
                    font-weight: bold;
                    color: #fff;
                }}
                .info-box {{
                    background: rgba(6, 182, 212, 0.1);
                    border: 1px solid rgba(6, 182, 212, 0.3);
                    border-radius: 8px;
                    padding: 15px;
                    margin: 20px 0;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid rgba(255, 255, 255, 0.1);
                    font-size: 14px;
                    color: #94a3b8;
                }}
                .timestamp {{
                    font-size: 12px;
                    color: #64748b;
                    margin-top: 10px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">SmartRisk</div>
                    <p style="color: #94a3b8; margin: 0;">Signal Alert Notification</p>
                </div>

                <h2 style="color: #fff; margin-bottom: 10px;">Hi {username}! 👋</h2>
                <p style="color: #cbd5e1;">A new trading signal has been generated matching your alert preferences:</p>

                <div class="signal-box">
                    <div style="font-size: 60px; margin-bottom: 10px;">{signal_emoji}</div>
                    <div class="signal-type">{signal_type}</div>
                    <div class="crypto-info">{crypto_display}</div>
                    <div class="timeframe">{timeframe_label} Timeframe</div>
                </div>

                <h3 style="color: #06b6d4; margin-bottom: 15px;">📊 Signal Details</h3>

                <div class="details-grid">
                    <div class="detail-box">
                        <div class="detail-label">Entry Price</div>
                        <div class="detail-value">${entry_price}</div>
                    </div>

                    <div class="detail-box">
                        <div class="detail-label">Target Price</div>
                        <div class="detail-value">${target}</div>
                    </div>

                    <div class="detail-box stop-loss">
                        <div class="detail-label">Stop Loss</div>
                        <div class="detail-value">${stop_loss}</div>
                    </div>
                </div>

                <div class="info-box">
                    <strong>💡 What to do next:</strong><br>
                    <p style="margin: 10px 0 0 0; color: #cbd5e1;">
                        Review the signal details above and consider your risk management strategy.
                        Log in to your SmartRisk account to see the complete chart analysis and additional signals.
                    </p>
                </div>

                <div class="timestamp">
                    Signal generated at: {timestamp}
                </div>

                <div class="footer">
                    <p><strong>⚙️ Manage Your Alerts</strong></p>
                    <p>You can update or disable your signal alerts anytime by logging into your SmartRisk account.</p>
                    <p style="margin-top: 20px;">
                        © 2026 SmartRisk. Powered by SmartRisk trading signals.
                    </p>
                    <p style="margin-top: 10px;">
                        <strong>Disclaimer:</strong> Trading cryptocurrencies carries risk.
                        Signals are for informational purposes only and not financial advice.
                    </p>
                    <p style="margin-top: 15px; font-size: 12px;">
                        Questions? Contact us at <a href="mailto:alberttyagi123@gmail.com" style="color: #06b6d4;">alberttyagi123@gmail.com</a>
                        or <a href="mailto:smarttriskfx@gmail.com" style="color: #06b6d4;">smarttriskfx@gmail.com</a>
                    </p>
                </div>
            </div>
        </body>
        </html>
            """

            text_body = f"""
SmartRisk - New Signal Alert

Hi {username}!

A new {signal_type} signal has been generated for {crypto_display} ({timeframe_label} timeframe).

Signal Details:
- Entry Price: ${entry_price}
- Target Price: ${target}
- Stop Loss:    ${stop_loss}
- Generated:    {timestamp}

Log in to your SmartRisk account to see the complete analysis.

© 2026 SmartRisk
Contact: alberttyagi123@gmail.com or smarttriskfx@gmail.com

Disclaimer: Trading cryptocurrencies carries risk. Signals are for informational purposes only.
            """

            part1 = MIMEText(text_body, "plain")
            part2 = MIMEText(html_body, "html")
            message.attach(part1)
            message.attach(part2)

            # FIX #5: SMTP with explicit timeout and retry on transient errors
            with smtplib.SMTP(smtp_server, smtp_port, timeout=30) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(sender_email, sender_password)
                server.sendmail(sender_email, email, message.as_string())

            logger.info(
                "✅ Email delivered → %s | %s %s %s",
                email, crypto_display, timeframe_raw, signal_type,
            )
            return True

        except smtplib.SMTPException as smtp_err:
            # FIX #5: retry on transient SMTP errors (421 temp unavail, 454 auth temp fail)
            error_code = getattr(smtp_err, 'smtp_code', 0)
            transient  = error_code in (421, 450, 451, 452, 454) or error_code == 0

            if transient and attempt < SMTP_MAX_RETRIES:
                logger.warning(
                    "⚠️  SMTP transient error (attempt %d/%d) for %s [%s]: %s — retrying in 5s",
                    attempt, SMTP_MAX_RETRIES, email, error_code, smtp_err,
                )
                time.sleep(5)
                continue   # retry

            logger.error(
                "❌ SMTP failed (attempt %d/%d) for %s: [code=%s] %s",
                attempt, SMTP_MAX_RETRIES, email, error_code, smtp_err, exc_info=True,
            )
            return False

        except Exception as e:
            logger.error(
                "❌ Failed to send email to %s (attempt %d/%d): %s",
                email, attempt, SMTP_MAX_RETRIES, e, exc_info=True,
            )
            return False

    return False   # exhausted retries


def notify_signal_subscribers(signal_data):
    """
    Notify all subscribers who have alerts matching the signal criteria.
    Each email is formatted in the subscriber's OWN saved timezone.

    Args:
        signal_data (dict): Signal information.
            'crypto' MUST already be in user-facing format (ETHUSD, XAUUSD, etc.)
            — signals.py normalizes it before calling this function.
            Do NOT re-normalize here (FIX #4).

    Returns:
        tuple[int, int]: (sent_count, failed_count)

    FIX #3: Detailed diagnostic logging before and after query.
    FIX #4: Removed double-normalization (crypto is already normalized).
    FIX #7: Fallback to user.email if alert.email is blank/stale.
    """
    from .models import SignalAlert

    crypto    = signal_data.get('crypto', '').strip()
    timeframe = signal_data.get('timeframe', '').strip()

    if not crypto or not timeframe:
        logger.warning("notify_signal_subscribers: missing crypto=%r or timeframe=%r", crypto, timeframe)
        return 0, 0

    # FIX #4: Do NOT re-normalize here. signals.py already normalized the symbol.
    # The old code did BINANCE_TO_USER.get(crypto.upper(), crypto.upper()) which
    # would turn "XAUUSD" into "XAUUSD" (ok by accident) but "paxgusdt" into
    # "paxgusdt" (wrong — no DB match). We receive a clean value, use it directly.

    # ── FIX #3: Diagnostic log BEFORE query ──────────────────────────────────
    logger.info(
        "📧 Querying subscribers: crypto=%r timeframe=%r is_active=True subscription=activated",
        crypto, timeframe,
    )

    alerts = SignalAlert.objects.filter(
        crypto=crypto,
        timeframe=timeframe,
        is_active=True,
        user__manual_subscription='activated',
    ).select_related('user')

    total_in_db = alerts.count()

    # ── FIX #3: Log query result details ─────────────────────────────────────
    if total_in_db == 0:
        # Run diagnostic sub-queries to explain WHY there are 0 results
        # so operators can diagnose without DB access
        all_for_crypto_tf = SignalAlert.objects.filter(
            crypto=crypto, timeframe=timeframe
        ).count()
        active_no_sub = SignalAlert.objects.filter(
            crypto=crypto, timeframe=timeframe, is_active=True,
        ).exclude(user__manual_subscription='activated').count()

        logger.warning(
            "⚠️  ZERO subscribers for %s %s — "
            "total_alerts_for_pair=%d  active_but_no_paid_sub=%d  "
            "Hint: check SignalAlert.crypto matches exactly, user.manual_subscription='activated', "
            "and SignalAlert.is_active=True",
            crypto, timeframe,
            all_for_crypto_tf, active_no_sub,
        )
        return 0, 0

    logger.info(
        "📬 Found %d active subscriber(s) for %s %s — sending emails",
        total_in_db, crypto, timeframe,
    )

    sent_count   = 0
    failed_count = 0

    for alert in alerts:
        try:
            user = alert.user

            # FIX #7: Use alert.email with fallback to user.email
            # alert.email may be stale if user changed their account email
            recipient_email = (alert.email or '').strip() or (user.email or '').strip()
            if not recipient_email:
                logger.warning(
                    "⚠️  No email address for user %s (alert_id=%d) — skipping",
                    user.username, alert.id,
                )
                failed_count += 1
                continue

            # Per-subscriber timezone for timestamp formatting
            user_tz = getattr(user, 'timezone', 'UTC') or 'UTC'

            logger.info(
                "📤 Sending to user=%s email=%s tz=%s",
                user.username, recipient_email, user_tz,
            )

            success = send_signal_alert_email(
                email=recipient_email,
                username=user.username,
                signal_data=signal_data,
                user_tz=user_tz,
            )

            if success:
                sent_count += 1
                logger.info(
                    "✅ Delivered: user=%s email=%s [%s %s %s]",
                    user.username, recipient_email,
                    crypto, timeframe, signal_data.get('signal_type'),
                )
            else:
                failed_count += 1
                # FIX #2: log WARNING for failed delivery so operators see it
                logger.warning(
                    "⚠️  DELIVERY FAILED: user=%s email=%s [%s %s %s] "
                    "— check SMTP error logged above",
                    user.username, recipient_email,
                    crypto, timeframe, signal_data.get('signal_type'),
                )

        except Exception as e:
            failed_count += 1
            logger.error(
                "❌ Unexpected error sending to user=%s: %s",
                getattr(alert, 'user', {username: '?'}).username if hasattr(alert, 'user') else '?',
                e, exc_info=True,
            )

    logger.info(
        "📊 Email summary for %s %s %s: sent=%d failed=%d total=%d",
        crypto, timeframe, signal_data.get('signal_type', '?'),
        sent_count, failed_count, total_in_db,
    )

    return sent_count, failed_count
