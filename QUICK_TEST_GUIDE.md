# 🚀 Quick Test Guide - AI Signals

## ✅ Rebuild Complete!
All services are running with the latest code.

---

## 📋 Test Checklist

### 1. Open Browser
```
http://localhost:3000
```

### 2. Hard Refresh (IMPORTANT!)
Clear browser cache to load new code:
- **Windows/Linux**: `Ctrl + Shift + R`
- **Mac**: `Cmd + Shift + R`

### 3. Check Console (F12)
Open Developer Tools → Console tab

**Expected Output**:
```
🚀 NeuralTrade Page Component Loaded - NEW VERSION
AI Signals WebSocket connected
Received AI signal: {asset: "BTCUSD", ...}
Received AI signal: {asset: "BTCUSD", ...}
Received AI signal: {asset: "BTCUSD", ...}
Received AI signal: {asset: "BTCUSD", ...}
```

### 4. Check UI

#### Connection Status (Top Right)
- ✅ Market: **Live** (green)
- ✅ Signals: **Live** (green)

#### Right Sidebar - Signal Statistics
```
Total: 4
BUY: 1 (green box)
SELL: 1 (red box)
HOLD: 1 (yellow box)
```

#### Chart (Center)
Look for colored markers:
- 🟢 Green arrow UP (↑) = BUY @ $78,800
- 🔴 Red arrow DOWN (↓) = SELL @ $79,200
- 🟡 Yellow circle (●) = HOLD @ $78,950
- 🟠 Orange circle (●) = STOP_LOSS @ $78,100

#### AI Signal Feed (Below Chart)
4 signal cards showing:
- Asset: BTCUSD
- Action: BUY/SELL/HOLD/STOP_LOSS
- Price: $78,xxx
- Message: "Agent A: ... | Agent B: ..."
- Timestamp

---

## ❌ If Signals Don't Show

### Quick Fix 1: Hard Refresh Again
```
Ctrl + Shift + R (or Cmd + Shift + R on Mac)
```

### Quick Fix 2: Clear All Browser Cache
1. Open DevTools (F12)
2. Right-click the refresh button
3. Select "Empty Cache and Hard Reload"

### Quick Fix 3: Check Backend
```powershell
# Check if signals exist in database
docker-compose -f docker-compose.prod.yml exec -T backend python -c "import django; import os; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'neuraltrade.settings'); django.setup(); from trading.models import MarketSignal; print(f'Signals: {MarketSignal.objects.filter(symbol=\"BTCUSD\").count()}')"
```

Should show: `Signals: 4`

### Quick Fix 4: Restart Frontend
```powershell
docker-compose -f docker-compose.prod.yml restart frontend
```

Wait 30 seconds, then refresh browser.

---

## 🎯 Success Indicators

| Check | Expected | Status |
|-------|----------|--------|
| Console message | "NEW VERSION" | ⬜ |
| WebSocket | "connected" | ⬜ |
| Signals received | 4 messages | ⬜ |
| Market status | Live (green) | ⬜ |
| Signal status | Live (green) | ⬜ |
| Chart markers | 4 visible | ⬜ |
| Signal feed | 4 cards | ⬜ |
| Signal counts | 4/1/1/1 | ⬜ |

---

## 🔄 Start Continuous Generation

Once all checks pass, start continuous signal generation:

```powershell
docker-compose -f docker-compose.prod.yml exec -d backend python ai_agents/management/commands/start_signals.py
```

This will generate new signals every 60 seconds.

---

## 📞 Need Help?

### View Backend Logs
```powershell
docker-compose -f docker-compose.prod.yml logs backend --tail 50 -f
```

### View Frontend Logs
```powershell
docker-compose -f docker-compose.prod.yml logs frontend --tail 50 -f
```

### Check All Services
```powershell
docker-compose -f docker-compose.prod.yml ps
```

---

## 🎉 Expected Result

After hard refresh, you should see a fully functional AI trading dashboard with:
- ✅ Live market data streaming
- ✅ 4 AI signals displayed on chart
- ✅ Signal feed showing all 4 signals
- ✅ Real-time WebSocket connections
- ✅ Signal statistics updated

**Now go test it!** 🚀
