# Signal Alerts - Quick Reference Card

## 🚀 Setup (One Command)

**Windows:**
```powershell
.\setup_signal_alerts.ps1
```

**Linux/Mac:**
```bash
./setup_signal_alerts.sh
```

## 🧪 Test

```bash
# Check system status
docker-compose exec backend python manage.py test_signal_alerts

# Send test email
docker-compose exec backend python manage.py test_signal_alerts \
  --email=your@email.com --username=YourName
```

## 📍 URLs

- **Frontend Page**: http://localhost/signal-alerts
- **API Endpoint**: http://localhost:8000/api/signal-alerts/
- **Subscription**: http://localhost/subscription

## 🔑 Access Requirements

| User Type | Can View Page | Can Activate Alerts |
|-----------|---------------|---------------------|
| Not Logged In | ❌ No | ❌ No |
| Trial User | ✅ Yes | ❌ No |
| Paid Subscriber | ✅ Yes | ✅ Yes |
| Expired Subscription | ✅ Yes | ❌ No |

## 📊 Supported Options

**Cryptocurrencies:**
- BTCUSD (Bitcoin)
- ETHUSD (Ethereum)
- LTCUSD (Litecoin)
- XRPUSD (Ripple)

**Timeframes:**
- 5m, 15m, 30m, 1h, 2h, 4h, 1d

## 📧 Email Content

Each alert email includes:
- ✅ Signal type (BUY/SELL)
- ✅ Cryptocurrency & timeframe
- ✅ Entry price
- ✅ Stop loss
- ✅ Target price
- ✅ Timestamp
- ✅ Link to dashboard

## 🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| Button disabled | Upgrade to paid subscription |
| No email received | Check spam folder, verify email settings |
| Alert not saving | Check browser console for errors |
| Email sending fails | Verify SMTP credentials in `.env` |

## 📝 API Examples

**Create Alert:**
```bash
curl -X POST http://localhost:8000/api/signal-alerts/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"crypto":"BTCUSD","timeframe":"1h","email":"user@example.com"}'
```

**Get Alerts:**
```bash
curl http://localhost:8000/api/signal-alerts/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 📞 Support

- alberttyagi123@gmail.com
- smarttriskfx@gmail.com

## ✅ Checklist

- [ ] Run setup script
- [ ] Test email sent successfully
- [ ] Create paid subscription user
- [ ] Set up alert on frontend
- [ ] Generate test signal
- [ ] Verify email received

**Done! 🎉**
