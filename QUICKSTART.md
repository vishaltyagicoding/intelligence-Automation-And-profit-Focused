# NeuralTrade - Quick Start Guide

## Phase 1: Core Infrastructure Setup Complete ✓

### What's Been Built

✅ **Django 5.0+ Project Structure** with professional organization
✅ **Django Channels 4.0** for async WebSocket handling
✅ **Redis Integration** as channel layer and cache
✅ **Celery with Beat** for automated tasks
✅ **Binance WebSocket Consumer** for real-time BTC/USDT streaming
✅ **Auto-Authentication System** for Shoonya & Binance
✅ **Risk Management** with slippage control
✅ **Docker Deployment** with docker-compose
✅ **Nginx Configuration** with WebSocket support
✅ **uvloop Integration** for 10k+ concurrent connections

### Project Structure

```
neuraltrade/
├── neuraltrade/          # Django settings & configuration
├── trading/              # Core trading logic & WebSocket consumers
├── market_data/          # Binance & Shoonya API clients
├── users/                # User management
├── risk_management/      # Slippage control & risk validation
├── scripts/              # Deployment scripts
├── nginx/                # Nginx configuration
└── docker-compose.yml    # Container orchestration
```

## Installation & Setup

### Option 1: Docker (Recommended)

```bash
# 1. Configure environment
cp .env.example .env
# Edit .env with your API credentials

# 2. Start all services
docker-compose up --build -d

# 3. Check status
docker-compose ps
docker-compose logs -f django

# 4. Access the platform
# API: http://localhost:8000
# Admin: http://localhost:8000/admin (admin/admin123)
# WebSocket: ws://localhost:8000/ws/market/BTCUSDT/
```

### Option 2: Manual Setup

```bash
# 1. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Setup database
createdb neuraltrade
python manage.py migrate

# 4. Create superuser
python manage.py createsuperuser

# 5. Start Redis
redis-server

# 6. Start Django (Terminal 1)
python manage.py runserver

# 7. Start Celery Worker (Terminal 2)
celery -A neuraltrade worker -l info

# 8. Start Celery Beat (Terminal 3)
celery -A neuraltrade beat -l info
```

## Configuration

### Required Environment Variables

Edit `.env` file:

```bash
# Binance API
BINANCE_API_KEY=your-binance-api-key
BINANCE_API_SECRET=your-binance-api-secret

# Shoonya/Finvasia API
SHOONYA_USER_ID=your-user-id
SHOONYA_PASSWORD=your-password
SHOONYA_TOTP_SECRET=your-totp-secret-for-2fa
SHOONYA_VENDOR_CODE=your-vendor-code
SHOONYA_API_KEY=your-api-key
SHOONYA_IMEI=your-imei

# Trading Configuration
MAX_TRADES_PER_DAY=4
SLIPPAGE_THRESHOLD_CRYPTO=0.0005    # 0.05%
SLIPPAGE_THRESHOLD_COMMODITY=0.001  # 0.1%
```

## Testing the System

### 1. Health Check

```bash
curl http://localhost:8000/api/trading/status/
```

Expected response:
```json
{
  "status": "healthy",
  "redis": "connected",
  "auth": {
    "shoonya": "active",
    "binance": "active"
  },
  "trading": {
    "active_trades": 0,
    "last_heartbeat": "2024-01-15T10:30:00Z"
  }
}
```

### 2. WebSocket Connection Test

Create `test_websocket.html`:

```html
<!DOCTYPE html>
<html>
<body>
<h1>NeuralTrade WebSocket Test</h1>
<div id="output"></div>

<script>
const ws = new WebSocket('ws://localhost:8000/ws/market/BTCUSDT/');

ws.onopen = () => {
  document.getElementById('output').innerHTML += '<p>Connected!</p>';
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  document.getElementById('output').innerHTML += 
    `<p>Price: ${data.price} | Qty: ${data.quantity}</p>`;
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};
</script>
</body>
</html>
```

### 3. Check Celery Tasks

```bash
# View scheduled tasks
docker-compose exec django python manage.py shell
>>> from django_celery_beat.models import PeriodicTask
>>> PeriodicTask.objects.all()

# Check Celery worker status
celery -A neuraltrade inspect active
```

## Key Features Implemented

### 1. Real-time Data Pipeline

- **Binance WebSocket Consumer** streams live BTC/USDT ticks
- **Redis TimeSeries** stores up to 10,000 recent ticks per symbol
- **Channel Layer** broadcasts to all connected clients
- **Non-blocking async** operations with uvloop

### 2. Auto-Authentication System

- **Shoonya Auto-Login**: Daily at 8:45 AM using TOTP
- **Binance Token Refresh**: Every 6 hours
- **Redis Token Storage**: Zero-latency access
- **Automatic Retry**: With exponential backoff

### 3. Market Watch Heartbeat

- **1-second interval** monitoring
- **Active trade tracking** in Redis
- **Stop-loss & target** monitoring
- **Automatic exit execution**

### 4. Risk Management

- **Slippage Control**: 0.05% for crypto, 0.1% for commodity
- **Position Size Limits**: Max 10% of balance
- **Daily Trade Limits**: Max 4 trades per day
- **Balance Validation**: Before each trade

### 5. High-Concurrency Support

- **uvloop**: High-performance event loop
- **10,000+ connections**: Per worker
- **Async WebSocket**: Non-blocking operations
- **Redis Channel Layer**: Efficient message broadcasting

## API Endpoints

```
GET  /api/trading/status/           # System health
GET  /api/trading/trades/           # List trades
POST /api/trading/trades/           # Create trade
GET  /api/trading/signals/          # AI signals
GET  /api/market/ohlcv/{symbol}/    # OHLCV data
GET  /api/users/profile/            # User profile
WS   /ws/market/{symbol}/           # Real-time data
```

## Celery Tasks Schedule

| Task | Schedule | Purpose |
|------|----------|---------|
| `auto_login_shoonya` | Daily 8:45 AM | Auto-login with TOTP |
| `refresh_binance_token` | Every 6 hours | Refresh API session |
| `market_watch_heartbeat` | Every 1 second | Monitor active trades |
| `cleanup_expired_tokens` | Daily midnight | Clean old data |

## Redis Keys

```
auth:binance:token              # Binance session (6h TTL)
auth:shoonya:token              # Shoonya session (24h TTL)
market:ticks:BTCUSDT            # Recent ticks (10k max)
market:heartbeat                # Last heartbeat timestamp
trades:active                   # Active trade IDs set
```

## Monitoring & Logs

```bash
# View Django logs
docker-compose logs -f django

# View Celery worker logs
docker-compose logs -f celery_worker

# View Celery beat logs
docker-compose logs -f celery_beat

# Redis monitoring
docker-compose exec redis redis-cli MONITOR

# Check Redis keys
docker-compose exec redis redis-cli KEYS '*'
```

## Troubleshooting

### WebSocket not connecting

1. Check Nginx configuration for WebSocket upgrade headers
2. Verify Django Channels is running
3. Check Redis connection

### Celery tasks not running

1. Verify Redis is running: `docker-compose ps redis`
2. Check Celery worker: `docker-compose logs celery_worker`
3. Restart beat: `docker-compose restart celery_beat`

### Database connection errors

1. Check PostgreSQL: `docker-compose logs db`
2. Verify credentials in `.env`
3. Run migrations: `docker-compose exec django python manage.py migrate`

## Next Steps (Phase 2)

Once Phase 1 is verified and running:

1. **CNN-LSTM AI Model** integration
2. **Feature Engineering** pipeline
3. **Trading Agent** implementation
4. **Advanced Risk Analytics**
5. **Flutter Mobile App** integration
6. **Backtesting Engine**
7. **Real-time P&L Dashboard**

## Documentation

- **README.md**: Project overview
- **DEPLOYMENT.md**: Detailed deployment guide
- **API_DOCUMENTATION.md**: Complete API reference
- **ARCHITECTURE.md**: System architecture details
- **PROJECT_STRUCTURE.md**: File structure explanation

## Support

For issues or questions:
1. Check logs: `docker-compose logs -f`
2. Verify configuration: `.env` file
3. Test components individually
4. Review documentation files

---

**Phase 1 Complete!** 🚀

The core infrastructure is ready for Phase 2 AI model integration.
