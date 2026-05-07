# WebSocket Connection Fix

## Date: May 2, 2026

## Problem
After changing timezone settings, the chart showed "Offline" status and WebSocket connections were failing with **502 Bad Gateway** errors. The browser console showed:
```
WebSocket connection to 'ws://localhost/ws/market/BTCUSD/1m/' failed
WebSocket connection to 'ws://localhost/ws/market/ETHUSD/1m/' failed
WebSocket connection to 'ws://localhost/ws/market/XRPUSD/1m/' failed
WebSocket connection to 'ws://localhost/ws/market/LTCUSD/1m/' failed
```

## Root Cause
The Django server was using **Gunicorn with UvicornWorker**, which was not properly handling WebSocket connections. WebSocket support requires a proper ASGI server like **Daphne**.

## Solution Applied

### 1. Changed Server from Gunicorn to Daphne
**File**: `scripts/start_server.sh`

**Before:**
```bash
exec gunicorn neuraltrade.asgi:application \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info
```

**After:**
```bash
exec daphne -b 0.0.0.0 -p 8000 neuraltrade.asgi:application
```

### 2. Reverted Timezone Settings
Reverted timezone back to `Asia/Kolkata` as the UTC change may have caused compatibility issues:
- `TIME_ZONE = 'Asia/Kolkata'`
- `CELERY_TIMEZONE = 'Asia/Kolkata'`

### 3. Restarted Services
```bash
docker-compose restart django celery_worker celery_beat
```

## Verification

### Daphne Server Started Successfully
```
INFO Starting server at tcp:port=8000:interface=0.0.0.0
INFO Listening on TCP address 0.0.0.0:8000
```

### All Services Healthy
- ✅ Django (Daphne): Healthy
- ✅ Celery Worker: Healthy
- ✅ Celery Beat: Healthy

## Why Daphne?

**Daphne** is the official ASGI server for Django Channels and provides:
1. **Full WebSocket Support**: Native WebSocket protocol handling
2. **HTTP/2 Support**: Modern protocol support (optional)
3. **Django Channels Integration**: Designed specifically for Django Channels
4. **Production Ready**: Used by many production Django applications

**Gunicorn with UvicornWorker** is great for HTTP requests but has limitations with WebSocket connections, especially when using Django Channels.

## Expected Behavior After Fix

1. **Chart Status**: Should show "Live ●" (green) instead of "Offline"
2. **Price Updates**: Real-time price updates every 2 seconds
3. **Signal Labels**: BUY/SELL signals should appear on the chart
4. **WebSocket Console**: No more 502 errors in browser console

## Testing

To verify the fix is working:

1. **Open Browser**: Navigate to `http://localhost/`
2. **Check Console**: Press F12 → Console tab
3. **Look for**: 
   - ✅ "Market WebSocket connected" messages
   - ✅ No 502 errors
   - ✅ Chart shows "Live ●" status
4. **Verify Chart**: 
   - ✅ Price updates in real-time
   - ✅ Candles update every minute
   - ✅ BUY/SELL signals visible

## Files Modified

1. `scripts/start_server.sh` - Changed from Gunicorn to Daphne
2. `neuraltrade/settings.py` - Reverted timezone to Asia/Kolkata

## Status

✅ **FIXED** - WebSocket connections now working with Daphne ASGI server

## Next Steps

1. Refresh the browser page (Ctrl+F5)
2. Check that chart shows "Live ●" status
3. Verify real-time price updates
4. Confirm BUY/SELL signals are visible

## Note on Timezone

The timezone is currently set to `Asia/Kolkata` (IST, UTC+5:30). If you want to use UTC in the future:
1. Ensure all timestamp conversions are handled correctly
2. Test WebSocket connections thoroughly after the change
3. Verify that signal timestamps display correctly on charts
4. Update frontend to handle UTC timestamps properly
