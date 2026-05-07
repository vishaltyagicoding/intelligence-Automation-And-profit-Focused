# NeuralTrade API Documentation

## Base URL

```
http://localhost:8000/api
```

## Authentication

All API endpoints require JWT authentication.

### Obtain Token

```http
POST /api/token/
Content-Type: application/json

{
  "username": "user",
  "password": "password"
}
```

**Response**:
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### Use Token

```http
GET /api/trading/trades/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

## Endpoints

### System Status

Get system health and status.

```http
GET /api/trading/status/
```

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "redis": "connected",
  "auth": {
    "shoonya": "active",
    "binance": "active"
  },
  "trading": {
    "active_trades": 5,
    "last_heartbeat": "2024-01-15T10:29:59Z"
  }
}
```

### Trades

#### List Trades

```http
GET /api/trading/trades/
```

**Query Parameters**:
- `status`: Filter by status (PENDING, EXECUTED, CANCELLED, FAILED)
- `market`: Filter by market (CRYPTO, COMMODITY)
- `page`: Page number

**Response**:
```json
{
  "count": 100,
  "next": "http://localhost:8000/api/trading/trades/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "symbol": "BTCUSDT",
      "market": "CRYPTO",
      "trade_type": "BUY",
      "quantity": "0.01",
      "entry_price": "45000.00",
      "exit_price": null,
      "stop_loss": "44000.00",
      "target": "46000.00",
      "status": "EXECUTED",
      "pnl": null,
      "slippage": "0.0002",
      "order_id": "ORD123456",
      "created_at": "2024-01-15T10:00:00Z",
      "executed_at": "2024-01-15T10:00:05Z",
      "closed_at": null
    }
  ]
}
```

#### Get Trade Details

```http
GET /api/trading/trades/{id}/
```

#### Create Trade

```http
POST /api/trading/trades/
Content-Type: application/json

{
  "symbol": "BTCUSDT",
  "market": "CRYPTO",
  "trade_type": "BUY",
  "quantity": "0.01",
  "entry_price": "45000.00",
  "stop_loss": "44000.00",
  "target": "46000.00",
  "order_id": "ORD123456"
}
```

### Market Signals

#### List Signals

```http
GET /api/trading/signals/
```

**Response**:
```json
{
  "count": 10,
  "results": [
    {
      "id": 1,
      "symbol": "BTCUSDT",
      "market": "CRYPTO",
      "signal": "BUY",
      "confidence": "85.50",
      "entry_price": "45000.00",
      "stop_loss": "44000.00",
      "target": "46000.00",
      "created_at": "2024-01-15T10:00:00Z",
      "is_executed": false
    }
  ]
}
```

### Market Data

#### Get OHLCV Data

```http
GET /api/market/ohlcv/{symbol}/
```

**Query Parameters**:
- `limit`: Number of candles (default: 100)

**Response**:
```json
[
  {
    "timestamp": "2024-01-15T10:00:00Z",
    "open": "45000.00",
    "high": "45100.00",
    "low": "44900.00",
    "close": "45050.00",
    "volume": "100.50"
  }
]
```

### User Profile

#### Get Profile

```http
GET /api/users/profile/
```

**Response**:
```json
{
  "username": "trader1",
  "email": "trader1@example.com",
  "phone": "+1234567890",
  "kyc_verified": true,
  "trading_enabled": true,
  "risk_level": "MEDIUM",
  "balance": "10000.00",
  "max_daily_trades": 4
}
```

## WebSocket API

### Market Data Stream

Connect to real-time market data:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/market/BTCUSDT/');

ws.onmessage = function(event) {
  const data = JSON.parse(event.data);
  console.log('Price:', data.price);
};

// Subscribe to different symbol
ws.send(JSON.stringify({
  action: 'subscribe',
  symbol: 'ETHUSDT'
}));
```

**Message Format**:
```json
{
  "symbol": "BTCUSDT",
  "price": 45000.50,
  "quantity": 0.5,
  "timestamp": 1705315200000,
  "is_buyer_maker": false
}
```

## Error Responses

### 400 Bad Request

```json
{
  "error": "Invalid request",
  "details": {
    "quantity": ["This field is required."]
  }
}
```

### 401 Unauthorized

```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden

```json
{
  "detail": "You do not have permission to perform this action."
}
```

### 500 Internal Server Error

```json
{
  "error": "Internal server error",
  "message": "An unexpected error occurred"
}
```

## Rate Limiting

- **API Endpoints**: 100 requests per minute
- **WebSocket**: 10,000 concurrent connections

## Pagination

All list endpoints support pagination:

```http
GET /api/trading/trades/?page=2&page_size=50
```

## Filtering & Sorting

```http
GET /api/trading/trades/?status=EXECUTED&ordering=-created_at
```

## Best Practices

1. **Always use HTTPS** in production
2. **Store tokens securely** (not in localStorage)
3. **Implement retry logic** for failed requests
4. **Handle WebSocket reconnection**
5. **Validate data** before sending
6. **Monitor rate limits**
