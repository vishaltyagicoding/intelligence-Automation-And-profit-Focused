# API Conventions

## Base URLs
- Production: `https://smartriskfx.com/api`
- Internal Docker: `http://django:8000/api`
- WebSocket: `wss://smartriskfx.com/ws`

## Auth
- Token: `access_token` in localStorage
- Header: `Authorization: Bearer <token>`

## Signal Endpoints

### GET /api/trading/reversal-zones/<symbol>/?timeframe=15m
Returns DB signals + at most 1 live_pending zone.
```json
{
  "success": true,
  "data": {
    "zones": [
      {
        "bar_index": 100,
        "center_price": 70253.92,
        "stop_loss": 69897.62,
        "target": 71027.57,
        "outer_top": 71027.57,
        "outer_bottom": 69897.62,
        "core_top": 70280.00,
        "core_bottom": 70230.00,
        "is_bullish": true,
        "label": "BUY",
        "timestamp": "2026-06-02T08:30:00+00:00",
        "source": "db"
      },
      {
        "source": "live_pending",
        "timestamp": "2026-06-02T09:45:00+00:00",
        ...
      }
    ],
    "status": {
      "last_signal": "Bullish Reversal",
      "tracking": "Monitoring Bearish Reversal"
    }
  }
}
```

### GET /api/trading/signal-history/<symbol>/?timeframe=15m
Returns DB signals with explicit stop_loss, target, center_price.
```json
{
  "success": true,
  "symbol": "BTCUSD",
  "timeframe": "15m",
  "signals": [
    {
      "bar_index": 100,
      "center_price": 70253.92,
      "stop_loss": 69897.62,
      "target": 71027.57,
      "outer_top": 71027.57,
      "outer_bottom": 69897.62,
      "is_bullish": true,
      "label": "BUY",
      "timestamp": "2026-06-02T08:30:00+00:00",
      "source": "db"
    }
  ]
}
```

## WebSocket
### URL: `wss://smartriskfx.com/ws/market/<symbol>/<timeframe>/`

### Kline message (price update)
```json
{"type": "kline", "asset": "BTCUSD", "timeframe": "15m", "price": 70360.01}
```

### Signal message (new BUY/SELL)
```json
{
  "type": "signal",
  "asset": "BTCUSD",
  "timeframe": "15m",
  "signal": "BUY",
  "is_bullish": true,
  "price": 70253.92,
  "tracking": "Monitoring Bearish Reversal",
  "all_zones": [
    {"is_bullish": true, "center_price": 70253.92, "stop_loss": 69897.62, "target": 71027.57, "timestamp": "..."}
  ]
}
```
**Frontend rule**: Only use `all_zones[all_zones.length - 1]` (newest zone). Never iterate all zones.

## Response Format
```json
{"success": true, "data": {...}}    // success
{"success": false, "error": "msg"} // error
```

## Binance Symbol Mapping
| Frontend | Binance API (api.binance.us) |
|---|---|
| BTCUSD | BTCUSDT |
| ETHUSD | ETHUSDT |
| XAUUSD | PAXGUSDT |
| LTCUSD | LTCUSDT |