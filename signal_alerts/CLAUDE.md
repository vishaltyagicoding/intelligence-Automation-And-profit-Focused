# Signal Alerts App Documentation

## Overview
The `signal_alerts` app manages user preferences for receiving email notifications when new trading signals are generated for specific symbols and timeframes.

## App Structure
```
signal_alerts/
├── __init__.py
├── models.py                    # SignalAlert model
├── serializers.py               # DRF serializers
├── views.py                     # API endpoints
├── email_utils.py               # Email sending utilities
├── urls.py                      # URL routing
├── admin.py                     # Django admin
└── management/
    └── commands/
        └── test_live_signal_email.py  # Test email command
```

## Models

### SignalAlert
Stores user preferences for signal notifications.

```python
class SignalAlert(models.Model):
    user = ForeignKey(User, on_delete=CASCADE)
    symbol = CharField(20)              # e.g., 'BTCUSD'
    timeframe = CharField(10)           # e.g., '15m'
    is_active = BooleanField(default=True)
    email_enabled = BooleanField(default=True)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    class Meta:
        unique_together = [['user', 'symbol', 'timeframe']]
        indexes = [
            Index(fields=['user', 'is_active']),
            Index(fields=['symbol', 'timeframe', 'is_active']),
        ]
```

**Unique Constraint**: One alert per user per symbol+timeframe combination

## API Endpoints

### 1. Get User Alerts
**Endpoint**: `GET /api/signal-alerts/`

**Headers**: `Authorization: Bearer <token>`

**Response**:
```json
{
  "alerts": [
    {
      "id": 1,
      "symbol": "BTCUSD",
      "timeframe": "15m",
      "is_active": true,
      "email_enabled": true,
      "created_at": "2026-05-11T12:00:00Z",
      "updated_at": "2026-05-11T12:00:00Z"
    },
    {
      "id": 2,
      "symbol": "ETHUSD",
      "timeframe": "1h",
      "is_active": true,
      "email_enabled": true,
      "created_at": "2026-05-11T12:00:00Z",
      "updated_at": "2026-05-11T12:00:00Z"
    }
  ]
}
```

### 2. Create/Update Alert
**Endpoint**: `POST /api/signal-alerts/`

**Headers**: `Authorization: Bearer <token>`

**Request**:
```json
{
  "symbol": "BTCUSD",
  "timeframe": "15m",
  "is_active": true,
  "email_enabled": true
}
```

**Response**:
```json
{
  "id": 1,
  "symbol": "BTCUSD",
  "timeframe": "15m",
  "is_active": true,
  "email_enabled": true,
  "message": "Alert created successfully"
}
```

**Behavior**:
- If alert exists → update
- If alert doesn't exist → create new

### 3. Delete Alert
**Endpoint**: `DELETE /api/signal-alerts/<id>/`

**Headers**: `Authorization: Bearer <token>`

**Response**:
```json
{
  "message": "Alert deleted successfully"
}
```

### 4. Test Email
**Endpoint**: `POST /api/signal-alerts/test-email/`

**Headers**: `Authorization: Bearer <token>`

**Request**:
```json
{
  "symbol": "BTCUSD",
  "timeframe": "15m"
}
```

**Response**:
```json
{
  "message": "Test email sent successfully"
}
```

**Purpose**: Send test email to verify email configuration

## Email Notification System

### Email Configuration
```python
# settings.py
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'smarttriskfx@gmail.com'
EMAIL_HOST_PASSWORD = '<gmail-app-password>'
DEFAULT_FROM_EMAIL = 'smarttriskfx@gmail.com'
```

### Email Template (HTML)
```html
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #06b6d4, #2563eb); color: white; padding: 20px; text-align: center; }
        .content { background: #f9fafb; padding: 20px; }
        .signal-box { background: white; border-left: 4px solid #10b981; padding: 15px; margin: 10px 0; }
        .buy { border-left-color: #10b981; }
        .sell { border-left-color: #ef4444; }
        .price { font-size: 24px; font-weight: bold; }
        .footer { text-align: center; padding: 20px; color: #6b7280; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚨 New {{ action }} Signal</h1>
            <p>{{ symbol }} ({{ timeframe }})</p>
        </div>
        <div class="content">
            <div class="signal-box {{ action|lower }}">
                <h2>Signal Details</h2>
                <p><strong>Symbol:</strong> {{ symbol }}</p>
                <p><strong>Timeframe:</strong> {{ timeframe }}</p>
                <p><strong>Action:</strong> {{ action }}</p>
                <p><strong>Entry Price:</strong> <span class="price">${{ entry_price }}</span></p>
                <p><strong>Stop Loss:</strong> ${{ stop_loss }}</p>
                <p><strong>Target:</strong> ${{ target }}</p>
                <p><strong>Time:</strong> {{ timestamp }}</p>
            </div>
        </div>
        <div class="footer">
            <p>SmartRisk - Cryptocurrency Trading Signals</p>
            <p><a href="https://smartriskfx.com">Visit Dashboard</a></p>
        </div>
    </div>
</body>
</html>
```

### Email Sending Logic
Located in `signal_alerts/email_utils.py`

```python
from django.core.mail import send_mail
from django.template.loader import render_to_string

def send_signal_email(user, signal_data):
    """
    Send signal notification email to user
    
    Args:
        user: User object
        signal_data: Dict with signal details
    """
    subject = f"🚨 New {signal_data['action']} Signal: {signal_data['symbol']} ({signal_data['timeframe']})"
    
    # Render HTML template
    html_message = render_to_string('signal_alerts/email_template.html', {
        'user': user,
        'symbol': signal_data['symbol'],
        'timeframe': signal_data['timeframe'],
        'action': signal_data['action'],
        'entry_price': signal_data['entry_price'],
        'stop_loss': signal_data['stop_loss'],
        'target': signal_data['target'],
        'timestamp': signal_data['timestamp'],
    })
    
    # Plain text fallback
    plain_message = f"""
    New {signal_data['action']} Signal
    
    Symbol: {signal_data['symbol']}
    Timeframe: {signal_data['timeframe']}
    Entry Price: ${signal_data['entry_price']}
    Stop Loss: ${signal_data['stop_loss']}
    Target: ${signal_data['target']}
    Time: {signal_data['timestamp']}
    
    Visit https://smartriskfx.com to view details.
    """
    
    send_mail(
        subject=subject,
        message=plain_message,
        from_email='smarttriskfx@gmail.com',
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )
```

## Integration with Signal Generation

### When Signal Fires
Located in `reversal_zones/tasks.py` → `_send_signal_notifications()`

**Process**:
1. New reversal zone detected
2. Query SignalAlert for matching symbol+timeframe
3. Filter for active alerts with email enabled
4. Filter for users with active subscriptions
5. Calculate entry, stop loss, target
6. Send email to each user
7. Log success/failure

**Code**:
```python
def _send_signal_notifications(zone, symbol, timeframe):
    from signal_alerts.models import SignalAlert
    from signal_alerts.email_utils import send_signal_email
    
    # Get all active alerts for this symbol+timeframe
    alerts = SignalAlert.objects.filter(
        symbol=symbol,
        timeframe=timeframe,
        is_active=True,
        email_enabled=True,
    ).select_related('user', 'user__userprofile')
    
    # Filter for activated users only
    activated_alerts = [
        alert for alert in alerts
        if alert.user.userprofile.manual_subscription == 'activated'
    ]
    
    for alert in activated_alerts:
        try:
            # Calculate prices
            entry = float(zone.center_price)
            if zone.is_bullish:
                target = float(zone.outer_top)
                calculate = target - entry
                stoploss = entry - (calculate * 0.5)
            else:
                target = float(zone.outer_bottom)
                calculate = entry - target
                stoploss = target + (calculate * 0.5)
            
            # Send email
            send_signal_email(alert.user, {
                'symbol': symbol,
                'timeframe': timeframe,
                'action': 'BUY' if zone.is_bullish else 'SELL',
                'entry_price': f"{entry:.2f}",
                'stop_loss': f"{stoploss:.2f}",
                'target': f"{target:.2f}",
                'timestamp': zone.reversal_time.strftime('%Y-%m-%d %H:%M:%S UTC'),
            })
            
            logger.info(f"✅ Email sent to {alert.user.email}")
        except Exception as e:
            logger.error(f"❌ Failed to send email to {alert.user.email}: {e}")
```

## Frontend Integration

### Alert Management Page
Location: `app/signal-alerts/page.tsx`

**Features**:
- View all user alerts
- Create new alerts
- Toggle alert on/off
- Delete alerts
- Test email functionality

**API Calls**:
```typescript
// Get alerts
const response = await fetch('/api/signal-alerts/', {
  headers: {
    'Authorization': `Bearer ${token}`,
  },
});

// Create/update alert
const response = await fetch('/api/signal-alerts/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    symbol: 'BTCUSD',
    timeframe: '15m',
    is_active: true,
    email_enabled: true,
  }),
});

// Test email
const response = await fetch('/api/signal-alerts/test-email/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    symbol: 'BTCUSD',
    timeframe: '15m',
  }),
});
```

## Testing

### Test Email Sending
```bash
# Via management command
sudo docker-compose exec django python manage.py test_live_signal_email

# Via Django shell
sudo docker-compose exec django python manage.py shell
>>> from signal_alerts.email_utils import send_signal_email
>>> from django.contrib.auth import get_user_model
>>> User = get_user_model()
>>> user = User.objects.get(email='test@example.com')
>>> send_signal_email(user, {
...     'symbol': 'BTCUSD',
...     'timeframe': '15m',
...     'action': 'BUY',
...     'entry_price': '50000.00',
...     'stop_loss': '49000.00',
...     'target': '52000.00',
...     'timestamp': '2026-05-11 12:00:00 UTC',
... })
```

### Test API Endpoint
```bash
# Get alerts
curl https://smartriskfx.com/api/signal-alerts/ \
  -H "Authorization: Bearer <token>"

# Create alert
curl -X POST https://smartriskfx.com/api/signal-alerts/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"symbol":"BTCUSD","timeframe":"15m","is_active":true,"email_enabled":true}'

# Test email
curl -X POST https://smartriskfx.com/api/signal-alerts/test-email/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"symbol":"BTCUSD","timeframe":"15m"}'
```

## Common Issues

### 1. Emails Not Sending
**Cause**: Gmail app password incorrect or 2FA not enabled
**Solution**:
1. Enable 2FA on Gmail account
2. Generate app password: https://myaccount.google.com/apppasswords
3. Update EMAIL_HOST_PASSWORD in .env
4. Restart Django container

### 2. User Not Receiving Emails
**Cause**: User subscription not activated
**Solution**: Admin must set `manual_subscription = 'activated'` in user profile

### 3. Duplicate Alerts
**Cause**: Unique constraint not enforced
**Solution**: Check database for duplicate entries, enforce unique_together

### 4. Wrong Prices in Email
**Cause**: Formula not applied correctly
**Solution**: Check calculation in `_send_signal_notifications()`

## Gmail App Password Setup

### Steps
1. Go to Google Account: https://myaccount.google.com
2. Security → 2-Step Verification (enable if not enabled)
3. App passwords: https://myaccount.google.com/apppasswords
4. Select app: Mail
5. Select device: Other (Custom name) → "SmartRisk"
6. Generate
7. Copy 16-character password
8. Update .env: `EMAIL_HOST_PASSWORD=<app-password>`
9. Restart: `sudo docker-compose restart django`

## Email Deliverability

### Best Practices
- Use verified sender email
- Include unsubscribe link (future)
- Avoid spam trigger words
- Keep email size reasonable
- Include plain text version
- Use proper HTML structure

### Monitoring
- Check Django logs for email errors
- Monitor Gmail sending limits (500/day for free accounts)
- Track bounce rates
- Monitor spam complaints
