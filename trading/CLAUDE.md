# Trading App Documentation

## Overview
The `trading` app is the core of SmartRisk, handling market data, signal generation, WebSocket connections, and API endpoints for reversal zones and signal history.

## App Structure
```
trading/
├── __init__.py
├── models.py              # Trade and MarketSignal models
├── serializers.py         # DRF serializers
├── views.py               # API endpoints
├── consumers.py           # WebSocket consumer
├── tasks.py               # Celery tasks
├── urls.py                # URL routing
├── admin.py               # Django admin
└── tests.py               # Unit tests
```

## Models

### Trade
Stores user trading activity.

```python
class Trade(models.Model):
    user = ForeignKey(User)
    symbol = CharField(20)              # e.g., 'BTCUSD'
    action = CharField(10)              # 'BUY' or 'SELL'
    entry_price = DecimalField(20, 8)
    stop_loss = DecimalField(20, 8)
    target = DecimalField(20, 8)
    quantity = DecimalField(20, 8)
    status = CharField(20)              # 'OPEN', 'CLOSED', 'CANCELLED'
    opened_at = DateTimeField
    closed_at = DateTimeField (optional)
    profit_loss = DecimalField(20, 8, optional)
    created_at = DateTimeField
```

### MarketSignal
Stores generated trading signals.

```python
class MarketSignal(models.Model):
    symbol = CharField(20)
    timeframe = CharField(10)
    action = CharField(10)              # 'BUY' or 'SELL'
    price = DecimalField(20, 8)
    stop_loss = DecimalField(20, 8)
    target = DecimalField(20, 8)
    status = CharField(20)              # 'OPEN', 'CLOSED'
    created_at = DateTimeField
    updated_at = DateTimeField
```

## API Endpoints

### 1. Get Reversal Zones
**Endpoint**: `GET /api/trading/reversal-zones/<symbol>/?timeframe=15m`

**Purpose**: Fetch live reversal zones for a symbol and timeframe

**Response**:
```json
{
  "success": true,
  "data": {
    "symbol": "BTCUSDT",
    "timeframe": "15m",
    "zones": [
      {
        "bar_index": 100,
        "center_price": 50000.00,
        "outer_top": 52000.00,
        "outer_bottom": 48000.00,
        "core_top": 51000.00,
        "core_bottom": 49000.00,
        "is_bullish": true,
        "label": "BUY",
        "timestamp": "2026-05-11T12:00:00Z",
        "source": "live"
      }
    ],
    "path_segments": [...],
    "status": {...},
    "live_count": 5
  }
}
```

**Process**:
1. Fetch OHLCV data from Binance.US
2. Run reversal zone calculator
3. Apply anti-chop filter
4. Return live zones only (no DB signals)
5. Cache result for 60 seconds

### 2. Get Signal History
**Endpoint**: `GET /api/trading/signal-history/<symbol>/?timeframe=15m`

**Purpose**: Fetch historical signals from database

**Response**:
```json
{
  "success": true,
  "symbol": "BTCUSDT",
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

**Filtering**:
- Minimum 1-hour gap between signals
- Strict alternation (BUY → SELL → BUY)
- Last 5 months of data

### 3. System Status
**Endpoint**: `GET /api/trading/system-status/`

**Purpose**: Health check and system status

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2026-05-11T12:00:00Z",
  "redis": "connected",
  "auth": {
    "shoonya": "inactive",
    "binance": "active"
  },
  "trading": {
    "active_trades": 0,
    "last_heartbeat": "2026-05-11T11:59:00Z"
  }
}
```

### 4. Trigger History Calculation
**Endpoint**: `POST /api/trading/calculate-history/<symbol>/`

**Purpose**: Manually trigger historical signal calculation

**Request**:
```json
{
  "timeframes": ["15m", "1h", "4h"]
}
```

**Response**:
```json
{
  "success": true,
  "symbol": "BTCUSD",
  "timeframes": ["15m", "1h", "4h"],
  "message": "Queued history calculation for BTCUSD × 3 timeframes"
}
```

## WebSocket Consumer

### Connection URL
```
wss://smartriskfx.com/ws/market/<symbol>/<timeframe>/
```

### Message Types

#### 1. Connection Status
```json
{
  "type": "connection",
  "status": "connected",
  "message": "Market WebSocket connected for BTCUSD at 15m timeframe"
}
```

#### 2. Price Update (Kline)
```json
{
  "type": "kline",
  "asset": "BTCUSD",
  "timeframe": "15m",
  "price": 50000.00,
  "timestamp": "2026-05-11T12:00:00Z",
  "open": 49500.00,
  "high": 50200.00,
  "low": 49300.00,
  "close": 50000.00,
  "volume": 1234.56
}
```

#### 3. Signal Alert
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

### Hybrid WebSocket + REST Fallback

**Problem**: WebSocket can send stale prices (same price repeatedly)

**Solution**: Implemented in `consumers.py`
1. Track last 3 prices received
2. If all 3 are identical → fetch fresh price from REST API
3. If no update for 30 seconds → fetch from REST API
4. Ensures prices ALWAYS update

**Code Location**: `trading/consumers.py` → `MarketConsumer.send_price_update()`

## Celery Tasks

### 1. Check Reversal Signals
**Task**: `trading.tasks.check_reversal_signals`

**Schedule**: Every 15 minutes

**Purpose**: 
- Fetch latest price data
- Calculate reversal zones
- Generate BUY/SELL signals
- Save to database
- Send email notifications
- Broadcast via WebSocket

### 2. Update Market Prices
**Task**: `trading.tasks.update_market_prices`

**Schedule**: Every 1 minute

**Purpose**:
- Fetch current prices from Binance.US
- Update Redis cache
- Broadcast to WebSocket clients

## Symbol Mapping

### XAUUSD → PAXGUSDT
Gold (XAUUSD) is mapped to PAXGUSDT (Paxos Gold) on Binance.

```python
ASSET_BINANCE_MAP = {
    'XAUUSD': 'PAXGUSDT'
}
```

### USD → USDT Conversion
```python
if symbol.endswith('USD') and not symbol.endswith('USDT'):
    binance_symbol = symbol[:-3] + 'USDT'
```

Examples:
- BTCUSD → BTCUSDT
- ETHUSD → ETHUSDT
- LTCUSD → LTCUSDT

## Binance.US Integration

### API Configuration
```python
from binance import AsyncClient

client = await AsyncClient.create(
    api_key=settings.BINANCE_API_KEY,
    api_secret=settings.BINANCE_API_SECRET,
    tld='us'  # IMPORTANT: Use Binance.US
)
```

### Fetch Klines
```python
klines = await client.get_klines(
    symbol='BTCUSDT',
    interval='15m',
    limit=1000
)
```

### REST API Endpoint
```
https://api.binance.us/api/v3/klines?symbol=BTCUSDT&interval=15m&limit=1000
```

## Caching Strategy

### Redis Cache Keys
- `reversal_zones_v4:<symbol>:<timeframe>` - Reversal zone data (60s TTL)
- `market:price:<symbol>` - Current price (10s TTL)
- `market:heartbeat` - Last update timestamp

### Cache Usage
```python
from django.core.cache import cache

# Set cache
cache.set(cache_key, data, timeout=60)

# Get cache
cached = cache.get(cache_key)
if cached:
    return Response(cached)
```

## Error Handling

### Binance API Errors
```python
try:
    response = requests.get(url, timeout=15)
    response.raise_for_status()
except requests.exceptions.Timeout:
    logger.error(f"❌ Binance API timeout")
    return Response({'error': 'Timeout'}, status=500)
except requests.exceptions.RequestException as e:
    logger.error(f"❌ Binance API error: {e}")
    return Response({'error': str(e)}, status=500)
```

### WebSocket Errors
```python
try:
    await self.send(text_data=json.dumps(message))
except Exception as e:
    logger.error(f"❌ WebSocket send error: {e}")
```

## Testing

### Test API Endpoint
```bash
curl https://smartriskfx.com/api/trading/reversal-zones/BTCUSD/?timeframe=15m
```

### Test WebSocket
```javascript
const ws = new WebSocket('wss://smartriskfx.com/ws/market/BTCUSD/15m/');
ws.onmessage = (e) => console.log(JSON.parse(e.data));
```

### Test Celery Task
```bash
sudo docker-compose exec django python manage.py shell
>>> from trading.tasks import check_reversal_signals
>>> check_reversal_signals.delay()
```

## Common Issues

### 1. Prices Not Updating
**Solution**: Check WebSocket fallback logic in `consumers.py`

### 2. Signals Not Generating
**Solution**: Check Celery worker is running
```bash
sudo docker-compose logs django | grep celery
```

### 3. Binance API Error
**Solution**: Ensure using `api.binance.us` with `tld='us'`

### 4. WebSocket Disconnecting
**Solution**: Check nginx WebSocket proxy configuration
