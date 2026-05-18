"""
Email Utility for Signal Alerts
================================
Sends email notifications when new trading signals are generated
"""
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from django.conf import settings

logger = logging.getLogger(__name__)


def send_signal_alert_email(email, username, signal_data, user_tz='UTC'):
    """
    Send signal alert email to user when a new signal is generated

    Args:
        email (str): Recipient email address
        username (str): User's username
        signal_data (dict): Signal information containing:
            - crypto: Cryptocurrency symbol
            - timeframe: Timeframe
            - signal_type: BUY or SELL
            - entry_price: Entry price
            - stop_loss: Stop loss level
            - target: Target level
            - timestamp: Signal generation time (UTC string, fallback)
            - timestamp_dt: raw UTC datetime object (preferred)
        user_tz (str): IANA timezone name for the recipient (e.g. 'Asia/Kolkata')

    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        import pytz
        # Email configuration
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        sender_email = settings.EMAIL_HOST_USER
        sender_password = settings.EMAIL_HOST_PASSWORD

        # Extract signal data — round all prices to 2 decimal places for clean display
        crypto       = signal_data.get('crypto', 'N/A')
        timeframe    = signal_data.get('timeframe', 'N/A')
        signal_type  = signal_data.get('signal_type', 'N/A')

        # ── Timezone-aware timestamp ──────────────────────────────────────────
        # Use the raw datetime if available so we can reformat in user's timezone.
        raw_dt = signal_data.get('timestamp_dt')
        try:
            tz = pytz.timezone(user_tz)
        except Exception:
            tz = pytz.utc

        if raw_dt is not None:
            local_dt = raw_dt.astimezone(tz)
            # e.g. "2026-05-17 22:15:00 IST"
            tz_label = local_dt.strftime('%Z')           # e.g. IST, EST, UTC
            timestamp = local_dt.strftime(f'%Y-%m-%d %H:%M:%S {tz_label}')
        else:
            # Fallback: use the pre-formatted UTC string
            timestamp = signal_data.get('timestamp', 'N/A')
        # ─────────────────────────────────────────────────────────────────────

        # Round prices to 2 decimal places so email matches history page exactly
        def _fmt_price(val):
            try:
                return f"{float(val):.2f}"
            except (TypeError, ValueError):
                return 'N/A'

        entry_price = _fmt_price(signal_data.get('entry_price'))
        target      = _fmt_price(signal_data.get('target'))

        raw_stop = signal_data.get('stop_loss')
        stop_loss = _fmt_price(raw_stop) if raw_stop not in (None, '', 0, 'N/A') else 'N/A'

        # Determine signal color and emoji
        if signal_type == 'BUY':
            signal_color = '#10b981'  # Green
            signal_emoji = '📈'
            signal_bg = 'rgba(16, 185, 129, 0.1)'
        else:
            signal_color = '#ef4444'  # Red
            signal_emoji = '📉'
            signal_bg = 'rgba(239, 68, 68, 0.1)'
        
        # Create message
        message = MIMEMultipart("alternative")
        message["Subject"] = f"🔔 New {signal_type} Signal: {crypto} ({timeframe})"
        message["From"] = f"SmartRisk Alerts <{sender_email}>"
        message["To"] = email
        
        # Email body (HTML)
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
                .cta-button {{
                    display: inline-block;
                    background: linear-gradient(135deg, #06b6d4 0%, #3b82f6 100%);
                    color: #fff;
                    padding: 15px 30px;
                    text-decoration: none;
                    border-radius: 8px;
                    font-weight: bold;
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
                    <div class="crypto-info">{crypto}</div>
                    <div class="timeframe">{timeframe} Timeframe</div>
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
                        Questions? Contact us at <a href="mailto:alberttyagi123@gmail.com" style="color: #06b6d4;">alberttyagi123@gmail.com</a> or <a href="mailto:smarttriskfx@gmail.com" style="color: #06b6d4;">smarttriskfx@gmail.com</a>
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Plain text version (fallback)
        text_body = f"""
        SmartRisk - New Signal Alert
        
        Hi {username}!
        
        A new {signal_type} signal has been generated for {crypto} ({timeframe} timeframe).
        
        Signal Details:
        - Entry Price: ${entry_price}
        - Target Price: ${target}
        - Stop Loss: ${stop_loss}
        - Generated: {timestamp}
        
        Log in to your SmartRisk account to see the complete analysis.
        
        © 2026 SmartRisk
        Contact: alberttyagi123@gmail.com or smarttriskfx@gmail.com
        
        Disclaimer: Trading cryptocurrencies carries risk. Signals are for informational purposes only.
        """
        
        # Attach both versions
        part1 = MIMEText(text_body, "plain")
        part2 = MIMEText(html_body, "html")
        message.attach(part1)
        message.attach(part2)
        
        # Send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, email, message.as_string())
        
        logger.info(f"✅ Signal alert email sent to {email} for {crypto} {timeframe} {signal_type}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to send signal alert email to {email}: {e}", exc_info=True)
        return False


def notify_signal_subscribers(signal_data):
    """
    Notify all subscribers who have alerts matching the signal criteria.
    Each email is formatted in the subscriber's OWN saved timezone.

    Args:
        signal_data (dict): Signal information (includes timestamp_dt for tz conversion)

    Returns:
        int: Number of notifications sent
    """
    from .models import SignalAlert

    crypto    = signal_data.get('crypto')
    timeframe = signal_data.get('timeframe')

    if not crypto or not timeframe:
        logger.warning("Signal data missing crypto or timeframe")
        return 0

    # Normalise crypto to user-facing format (BTCUSD not BTCUSDT)
    BINANCE_TO_USER = {
        'BTCUSDT': 'BTCUSD', 'ETHUSDT': 'ETHUSD',
        'LTCUSDT': 'LTCUSD', 'PAXGUSDT': 'XAUUSD', 'XAUUSDT': 'XAUUSD',
    }
    crypto = BINANCE_TO_USER.get(crypto.upper(), crypto.upper())

    # Find all active alerts matching this signal (paid subscribers only)
    alerts = SignalAlert.objects.filter(
        crypto=crypto,
        timeframe=timeframe,
        is_active=True,
        user__manual_subscription='activated'
    ).select_related('user')

    notifications_sent = 0

    for alert in alerts:
        try:
            # Use the subscriber's saved timezone (set by browser on login).
            # Falls back to 'UTC' if not yet populated.
            user_tz = getattr(alert.user, 'timezone', 'UTC') or 'UTC'

            success = send_signal_alert_email(
                email=alert.email,
                username=alert.user.username,
                signal_data=signal_data,
                user_tz=user_tz,           # ← per-subscriber local timezone
            )
            if success:
                notifications_sent += 1
        except Exception as e:
            logger.error(f"Error sending alert to {alert.user.username}: {e}")

    logger.info(f"📧 Sent {notifications_sent} signal alert notifications for {crypto} {timeframe}")
    return notifications_sent