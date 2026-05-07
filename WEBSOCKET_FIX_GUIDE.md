# WebSocket Connection Fix Guide

## Problem Summary
WebSocket connections were disconnecting frequently, causing stuck prices and $0.0000 values. This was due to:

1. **Missing Binance API credentials** - The `.env` file had placeholder values
2. **Aggressive timeout settings** - 65-second timeout was too short for 1-minute kline updates
3. **No keepalive mechanism** - Connections would timeout without activity
4. **Insufficient error handling** - Reconnection logic needed improvement

## What Was Fixed

### Backend Changes (`trading/consumers.py`)
1. **Increased timeout from 65s to 90s** - Binance sends kline updates every ~60 seconds
2. **Increased reconnection threshold from 120s to 180s** - More tolerance for network delays
3. **Added ping/pong keepalive** - Server now sends ping messages to keep connection alive
4. **Added pong handler** - Server can receive pong responses from clients
5. **Better error logging** - More detailed logs for debugging

### Frontend Changes (`app/page.tsx` and `components/ChartComponent.tsx`)
1. **Added ping/pong handlers** - Clients now respond to server ping messages
2. **Improved message parsing** - Better handling of different message types
3. **Enhanced logging** - Console logs show ping/pong activity

## Required Setup: Binance API Credentials

**CRITICAL**: You MUST set up real Binance API credentials for the WebSocket to work properly.

### Step 1: Create Binance API Keys

1. Go to [Binance](https://www.binance.com/) and log in
2. Navigate to **API Management** (Profile → API Management)
3. Click **Create API**
4. Choose **System generated** API key
5. Give it a label like "NeuralTrade WebSocket"
6. Complete 2FA verification
7. **IMPORTANT**: Copy both the API Key and Secret Key immediately (you won't see the secret again)

### Step 2: Configure API Key Permissions

For WebSocket market data, you only need:
- ✅ **Enable Reading** (checked)
- ❌ **Enable Spot & Margin Trading** (unchecked - not needed for read-only data)
- ❌ **Enable Futures** (unchecked)
- ❌ **Enable Withdrawals** (unchecked)

### Step 3: Update `.env` File

Open your `.env` file and replace the placeholder values:

```bash
# Binance API (Required for WebSocket market data)
BINANCE_API_KEY=your_actual_api_key_here
BINANCE_API_SECRET=your_actual_secret_key_here
```

**Example** (with fake keys):
```bash
BINANCE_API_KEY=K8xJ9mN2pQ4rS6tU8vW0xY2zA4bC6dE8fG0hI2jK4lM6nO8pQ0rS2tU4vW6xY8z
BINANCE_API_SECRET=A0bC2dE4fG6hI8jK0lM2nO4pQ6rS8tU0vW2xY4zA6bC8dE0fG2hI4jK6lM8nO0p
```

### Step 4: Restart Docker Containers

After updating `.env`, restart the containers:

```powershell
# Stop all containers
docker-compose -f docker-compose.prod.yml down

# Rebuild and start (to pick up new environment variables)
docker-compose -f docker-compose.prod.yml up -d --build backend

# Check logs to verify connection
docker-compose -f docker-compose.prod.yml logs -f backend
```

## Verification

### Check Backend Logs
```powershell
docker-compose -f docker-compose.prod.yml logs -f backend
```

**Good signs:**
```
INFO Kline stream opened for BTCUSD
INFO Kline processed for BTCUSD: close=74954.85
DEBUG Keepalive check for BTCUSD
```

**Bad signs:**
```
ERROR Error starting Binance stream for BTCUSD: Invalid API-key, IP, or permissions
ERROR Error in Binance stream for BTCUSD: Connection refused
```

### Check Frontend Console
Open browser DevTools (F12) and check Console:

**Good signs:**
```
WebSocket opened for BTCUSD
Chart update for BTCUSD: 74954.85 at 2026-04-17T...
Sent pong for BTCUSD
```

**Bad signs:**
```
WebSocket closed for BTCUSD, code: 1006
WebSocket error for BTCUSD
Invalid price received: 0
```

### Check Website
1. Open http://localhost:3000
2. **Watchlist prices** should show real values (not $0.0000)
3. **Market status** should show "Connected" (green)
4. **Chart** should show live candles updating every minute
5. **Last Price** should update in real-time

## Troubleshooting

### Issue: Still showing $0.0000 prices

**Cause**: Binance API credentials are invalid or not set

**Solution**:
1. Verify API key and secret in `.env` are correct (no extra spaces)
2. Check API key permissions on Binance (must have "Enable Reading")
3. Restart backend container: `docker-compose -f docker-compose.prod.yml restart backend`

### Issue: Prices stuck for 5+ minutes

**Cause**: WebSocket disconnected and not reconnecting

**Solution**:
1. Check backend logs: `docker-compose -f docker-compose.prod.yml logs backend | grep "WebSocket"`
2. Refresh the browser page (F5)
3. Check if Redis is running: `docker-compose -f docker-compose.prod.yml ps redis`

### Issue: Prices fluctuating too fast

**Cause**: This was the old issue with trade stream (individual ticks)

**Solution**: Already fixed - now using 1-minute kline stream instead of trade stream

### Issue: WebSocket keeps disconnecting

**Possible causes**:
1. **Network issues** - Check your internet connection
2. **Binance API rate limits** - You might be hitting rate limits (unlikely with just 4 assets)
3. **Docker network issues** - Restart all containers

**Solution**:
```powershell
# Restart all services
docker-compose -f docker-compose.prod.yml restart

# Or rebuild everything
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d --build
```

## Testing Without Binance API

If you want to test without Binance API credentials, the system will still work but:
- WebSocket will connect to Binance public streams (no auth required)
- You'll see warnings in logs but data should still flow
- Some rate limits may apply

However, for production use, **you should always use API credentials** for better reliability and higher rate limits.

## Rate Limits

With API credentials:
- **WebSocket connections**: 300 per 5 minutes
- **Weight**: 1 per connection (very low)
- **Current usage**: 4 connections (BTCUSD, ETHUSD, XRPUSD, LTCUSD)

You're well within limits, so rate limiting should not be an issue.

## Next Steps

1. ✅ Set up Binance API credentials in `.env`
2. ✅ Restart backend container
3. ✅ Verify WebSocket connections in logs
4. ✅ Check website shows live prices
5. ✅ Monitor for 10-15 minutes to ensure stability

## Support

If issues persist after following this guide:
1. Check backend logs for specific error messages
2. Check browser console for frontend errors
3. Verify all Docker containers are running: `docker-compose -f docker-compose.prod.yml ps`
4. Check Redis connection: `docker-compose -f docker-compose.prod.yml exec redis redis-cli ping`

The system should now maintain stable WebSocket connections with proper keepalive and reconnection logic.
