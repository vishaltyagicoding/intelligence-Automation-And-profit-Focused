# API Conventions

## Base URLs

### Production
- **Frontend**: https://smartriskfx.com
- **Backend API**: https://smartriskfx.com/api
- **WebSocket**: wss://smartriskfx.com/ws

### Local Development
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000/api
- **WebSocket**: ws://localhost:8000/ws

## Authentication

### Token-Based Auth
- **Token Name**: `access_token` (stored in localStorage)
- **Header**: `Authorization: Bearer <token>`
- **Login Endpoint**: `POST /api/auth/login/`
- **Register Endpoint**: `POST /api/auth/register/`

### Request Example
```typescript
const response = await fetch('/api/endpoint/', {
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json',
  },
});
```

## API Endpoints

### Authentication
- `POST /api/auth/register/` - User registration
- `POST /api/auth/login/` - User login
- `POST /api/auth/logout/` - User logout
- `GET /api/auth/user/` - Get current user
- `POST /api/auth/verify-email/` - Verify email
- `POST /api/auth/forgot-password/` - Request password reset
- `POST /api/auth/reset-password/` - Reset password

### Trading Signals
- `GET /api/trading/reversal-zones/<symbol>/?timeframe=15m` - Get live reversal zones
- `GET /api/trading/signal-history/<symbol>/?timeframe=15m` - Get historical signals
- `POST /api/trading/calculate-history/<symbol>/` - Trigger history calculation

### Signal Alerts
- `GET /api/signal-alerts/` - Get user's alert preferences
- `POST /api/signal-alerts/` - Create/update alert preferences
- `POST /api/signal-alerts/test-email/` - Send test email

### Subscription
- `GET /api/subscription/status/` - Get subscription status
- `POST /api/subscription/activate/` - Activate subscription

### Health Check
- `GET /api/health/` - Backend health check
- `GET /api/trading/system-status/` - System status

## Response Format

### Success Response
```json
{
  "success": true,
  "data": {
    "symbol": "BTCUSD",
    "zones": [...]
  }
}
```

### Error Response
```json
{
  "success": false,
  "error": "Error message here"
}
```

### Signal History Response
```json
{
  "success": true,
  "symbol": "BTCUSD",
  "timeframe": "15m",
  "count": 10,
  "signals": [
    {
      "bar_index": 100,
      "is_bullish": true,
      "center_price": 50000.00,
      "stop_loss": 49000.00,
      "target": 52000.00,
      "outer_top": 52000.00,
      "outer_bottom": 48000.00,
      "core_top": 51000.00,
      "core_bottom": 49000.00,
      "label": "BUY",
      "timestamp": "2026-05-11T12:00:00Z"
    }
  ]
}
```

## WebSocket Protocol

### Connection URL
```
wss://smartriskfx.com/ws/market/<symbol>/<timeframe>/
```

### Message Types

#### Price Update (Kline)
```json
{
  "type": "kline",
  "asset": "BTCUSD",
  "timeframe": "15m",
  "price": 50000.00,
  "timestamp": "2026-05-11T12:00:00Z"
}
```

#### Signal Alert
```json
{
  "type": "signal",
  "asset": "BTCUSD",
  "timeframe": "15m",
  "is_bullish": true,
  "price": 50000.00,
  "stop_loss": 49000.00,
  "target": 52000.00,
  "timestamp": "2026-05-11T12:00:00Z"
}
```

#### Connection Status
```json
{
  "type": "connection",
  "status": "connected",
  "message": "Market WebSocket connected for BTCUSD at 15m timeframe"
}
```

## Rate Limiting
- No rate limiting currently implemented
- Future: 100 requests per minute per user

## CORS Configuration
- Allowed Origins: `https://smartriskfx.com`, `http://localhost:3000`
- Allowed Methods: GET, POST, PUT, DELETE, OPTIONS
- Allowed Headers: Authorization, Content-Type

## Error Codes
- `400` - Bad Request (invalid parameters)
- `401` - Unauthorized (missing/invalid token)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `500` - Internal Server Error
- `503` - Service Unavailable

## Pagination
Currently not implemented. All endpoints return full datasets.
Future: Use `?page=1&limit=50` query parameters.

## Filtering
Use query parameters for filtering:
- `?symbol=BTCUSD` - Filter by symbol
- `?timeframe=15m` - Filter by timeframe
- `?action=BUY` - Filter by action type
- `?status=OPEN` - Filter by status
