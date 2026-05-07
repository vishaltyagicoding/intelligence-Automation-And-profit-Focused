# 🚀 Delta Exchange - Quick Start

## ⚠️ SECURITY ALERT

**YOU SHARED API KEYS PUBLICLY!**

**DO THIS NOW:**
1. Go to: https://www.delta.exchange/app/account/api
2. Revoke exposed keys
3. Generate new keys
4. Never share again!

---

## ✅ 5-Minute Setup

### Step 1: Get New API Keys (2 min)
```
1. Login to Delta Exchange
2. Account → API Management
3. Create New API Key
4. Enable: Read + Trade
5. Disable: Withdraw
6. Copy API Key and Secret
```

### Step 2: Add to .env (1 min)
```bash
nano .env

# Add these lines:
DELTA_API_KEY=your_new_key_here
DELTA_API_SECRET=your_new_secret_here
```

### Step 3: Restart (1 min)
```bash
docker-compose restart django celery_worker
```

### Step 4: Test (1 min)
```bash
python manage.py shell

>>> from market_data.delta_client import DeltaExchangeClient
>>> from django.conf import settings
>>> client = DeltaExchangeClient(settings.DELTA_API_KEY, settings.DELTA_API_SECRET)
>>> client.test_connection()
True

>>> symbols = client.get_available_symbols()
>>> print(len(symbols))
100+
```

---

## 🎯 What You Can Trade

### Perpetual Futures (100+ pairs)
- BTCUSDT, ETHUSDT, BNBUSDT
- ADAUSDT, XRPUSDT, SOLUSDT
- DOGEUSDT, DOTUSDT, MATICUSDT
- And 90+ more!

### Futures Contracts
- Quarterly (BTC, ETH)
- Monthly (BTC, ETH)

### Options
- BTC Call/Put
- ETH Call/Put

---

## 📡 Quick Usage

### WebSocket (Real-time)
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/delta/BTCUSDT/');
ws.onmessage = (e) => console.log(JSON.parse(e.data));
```

### REST API (Python)
```python
from market_data.delta_client import DeltaExchangeClient

client = DeltaExchangeClient(api_key, api_secret)

# Get data
ticker = client.get_ticker('BTCUSDT')
balance = client.get_balance()

# Trade
order = client.place_order(
    symbol='BTCUSDT',
    side='buy',
    order_type='market_order',
    size=0.001
)
```

### AI Trading
```bash
curl -X POST http://localhost:8000/api/ai/analyze/ \
  -H "Content-Type: application/json" \
  -d '{"symbol":"BTCUSDT","exchange":"DELTA"}'
```

---

## 📚 Full Documentation

- **DELTA_EXCHANGE_GUIDE.md** - Complete guide
- **DELTA_INTEGRATION_SUMMARY.md** - Summary
- **market_data/delta_client.py** - API client code

---

## ✅ Checklist

- [ ] Revoked exposed API keys
- [ ] Generated new API keys
- [ ] Added to .env file
- [ ] Restarted services
- [ ] Tested connection
- [ ] Verified symbols available
- [ ] Ready to trade!

---

**🔒 Remember: NEVER share API keys!**
