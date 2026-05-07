# Signal Alerts System - Complete Guide

## 📋 Overview

The Signal Alerts system allows **paid subscribers** to receive instant email notifications when new trading signals are generated for their selected cryptocurrency and timeframe combinations.

## ✨ Features

- **Real-time Email Notifications** - Get instant alerts when signals match your preferences
- **Customizable Alerts** - Choose specific crypto + timeframe combinations
- **Professional Email Design** - Beautiful HTML emails with complete signal details
- **Access Control** - Only available for paid subscribers (not trial users)
- **Multiple Alerts** - Set up alerts for different crypto/timeframe pairs
- **Easy Management** - Enable/disable alerts anytime from the dashboard

## 🎯 Who Can Use Signal Alerts?

### ✅ Eligible Users:
- **Paid Subscribers** with active subscription
- Users with `subscription_status.is_active = True` AND `subscription_status.is_trial = False`

### ❌ Not Eligible:
- **Trial Users** - Must upgrade to paid subscription
- **Expired Subscriptions** - Must renew subscription
- **Non-Subscribers** - Must activate subscription

## 🚀 Setup Instructions

### 1. Run the Setup Script

**Windows (PowerShell):**
```powershell
.\setup_signal_alerts.ps1
```

**Linux/Mac:**
```bash
chmod +x setup_signal_alerts.sh
./setup_signal_alerts.sh
```

### 2. Manual Setup (if script fails)

```bash
# Create migrations
docker-compose exec backend python manage.py makemigrations signal_alerts

# Run migrations
docker-compose exec backend python manage.py migrate signal_alerts

# Test the system
docker-compose exec backend python manage.py test_signal_alerts
```

## 📧 How It Works

### 1. User Creates Alert
- User visits `/signal-alerts` page
- Selects cryptocurrency (BTCUSD, ETHUSD, LTCUSD, XRPUSD)
- Selects timeframe (5m, 15m, 30m, 1h, 2h, 4h, 1d)
- Clicks "Activate Signal Alert" button
- Alert is saved to database

### 2. Signal Generation
- When a new trading signal is generated (BUY/SELL)
- System checks for matching alerts in database
- Filters for active paid subscribers only

### 3. Email Notification
- Email sent to all matching subscribers
- Contains complete signal details:
  - Signal type (BUY/SELL)
  - Entry price
  - Stop loss
  - Target price
  - Timestamp
- Professional HTML design with branding

## 🧪 Testing

### Test with Specific Email
```bash
docker-compose exec backend python manage.py test_signal_alerts \
  --email=your@email.com \
  --username=YourName
```

### Check System Status
```bash
docker-compose exec backend python manage.py test_signal_alerts
```

This will show:
- Active signal alerts
- Paid subscribers
- Test notification results

## 📊 Database Schema

### SignalAlert Model
```python
{
    'user': ForeignKey(User),
    'crypto': CharField(choices=['BTCUSD', 'ETHUSD', 'LTCUSD', 'XRPUSD']),
    'timeframe': CharField(choices=['5m', '15m', '30m', '1h', '2h', '4h', '1d']),
    'email': EmailField,
    'is_active': BooleanField(default=True),
    'created_at': DateTimeField(auto_now_add=True),
    'updated_at': DateTimeField(auto_now=True),
}
```

### Unique Constraint
- One alert per user/crypto/timeframe combination
- Updating an existing alert will modify the email address

## 🔌 API Endpoints

### Create/Update Alert
```http
POST /api/signal-alerts/
Authorization: Bearer <token>
Content-Type: application/json

{
  "crypto": "BTCUSD",
  "timeframe": "1h",
  "email": "user@example.com"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Signal alert activated successfully",
  "alert": {
    "crypto": "BTCUSD",
    "timeframe": "1h",
    "email": "user@example.com",
    "is_active": true
  }
}
```

### Get User's Alerts
```http
GET /api/signal-alerts/
Authorization: Bearer <token>
```

**Response:**
```json
{
  "alerts": [
    {
      "id": 1,
      "crypto": "BTCUSD",
      "timeframe": "1h",
      "email": "user@example.com",
      "created_at": "2026-05-06T10:30:00Z"
    }
  ],
  "count": 1
}
```

### Deactivate Alert
```http
DELETE /api/signal-alerts/
Authorization: Bearer <token>
Content-Type: application/json

{
  "alert_id": 1
}
```

## 🎨 Frontend Pages

### Signal Alerts Page (`/signal-alerts`)
- **Location**: `app/signal-alerts/page.tsx`
- **Features**:
  - Cryptocurrency selection grid
  - Timeframe selection grid
  - Current configuration summary
  - Subscription status banner
  - Success/error feedback
  - Feature highlights

### Navigation Integration
- Added to main navbar (when authenticated)
- Added to user profile dropdown
- Bell icon (🔔) for easy identification

## 📝 Email Template

### HTML Email Includes:
- SmartRisk branding
- Signal type with emoji (📈 BUY / 📉 SELL)
- Cryptocurrency and timeframe
- Entry price, stop loss, target
- Timestamp
- Call-to-action button to dashboard
- Manage alerts link
- Disclaimer and contact information

### Plain Text Fallback
- Simple text version for email clients that don't support HTML
- Contains all essential information

## 🔧 Configuration

### Email Settings
Configured in `neuraltrade/settings.py`:
```python
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', 'alberttyagi123@gmail.com')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
```

### Supported Cryptocurrencies
- BTCUSD (Bitcoin)
- ETHUSD (Ethereum)
- LTCUSD (Litecoin)
- XRPUSD (Ripple)

### Supported Timeframes
- 5m (5 Minutes)
- 15m (15 Minutes)
- 30m (30 Minutes)
- 1h (1 Hour)
- 2h (2 Hours)
- 4h (4 Hours)
- 1d (1 Day)

## 🐛 Troubleshooting

### No Emails Received
1. **Check subscription status**: Must be paid subscriber (not trial)
2. **Check alert is active**: Visit `/signal-alerts` to verify
3. **Check email settings**: Verify EMAIL_HOST_USER and EMAIL_HOST_PASSWORD in `.env`
4. **Check spam folder**: Emails might be filtered
5. **Check logs**: `docker-compose logs backend | grep "signal alert"`

### Button Disabled
- **Reason**: User is on trial or has no active subscription
- **Solution**: Upgrade to paid subscription at `/subscription`

### Alert Not Saving
1. **Check authentication**: Must be logged in
2. **Check API response**: Open browser console for errors
3. **Check backend logs**: `docker-compose logs backend`

### Email Sending Fails
1. **Check SMTP credentials**: Verify Gmail app password
2. **Check network**: Ensure backend can reach smtp.gmail.com:587
3. **Check rate limits**: Gmail has sending limits

## 📈 Performance

### Email Sending
- **Non-blocking**: Emails sent in background thread
- **No impact on signal generation**: Async execution
- **Error handling**: Failures logged but don't affect signals

### Database Queries
- **Optimized**: Uses `select_related` for user data
- **Indexed**: Unique constraint creates index
- **Filtered**: Only queries active alerts for paid users

## 🔒 Security

### Access Control
- **Authentication required**: All endpoints require valid JWT token
- **User isolation**: Users can only manage their own alerts
- **Subscription validation**: Backend verifies paid subscription status

### Email Security
- **TLS encryption**: All SMTP connections use TLS
- **No sensitive data**: Emails don't contain passwords or tokens
- **Rate limiting**: Prevents spam/abuse

## 📚 Code Structure

```
signal_alerts/
├── __init__.py
├── admin.py                    # Django admin interface
├── apps.py                     # App configuration
├── models.py                   # SignalAlert model
├── views.py                    # API endpoints
├── urls.py                     # URL routing
├── email_utils.py              # Email sending functions
├── migrations/
│   ├── __init__.py
│   └── 0001_initial.py        # Initial migration
└── management/
    └── commands/
        └── test_signal_alerts.py  # Testing command
```

## 🎯 Future Enhancements

### Potential Features:
- SMS notifications (Twilio integration)
- Push notifications (mobile app)
- Telegram bot integration
- Discord webhook integration
- Alert history/analytics
- Multiple email addresses per alert
- Custom alert conditions (price thresholds, etc.)
- Alert scheduling (only during trading hours)

## 📞 Support

### Contact Information:
- **Email**: alberttyagi123@gmail.com
- **Email**: smarttriskfx@gmail.com

### Documentation:
- **API Docs**: http://localhost:8000/
- **Signal Alerts Page**: http://localhost/signal-alerts
- **Subscription Page**: http://localhost/subscription

## ✅ Checklist

Before going live, ensure:
- [ ] Migrations run successfully
- [ ] Email credentials configured in `.env`
- [ ] Test email sent successfully
- [ ] Frontend page loads correctly
- [ ] API endpoints respond correctly
- [ ] Subscription validation works
- [ ] Email template renders properly
- [ ] Navigation links work
- [ ] Mobile responsive design tested
- [ ] Error handling tested
- [ ] Logs configured properly

## 🎉 Success!

Your Signal Alerts system is now ready! Users can:
1. Visit `/signal-alerts`
2. Select their preferences
3. Activate alerts
4. Receive instant email notifications for new signals

**Happy Trading! 📈**
