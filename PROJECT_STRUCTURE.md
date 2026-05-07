# NeuralTrade Project Structure

```
neuraltrade/
├── neuraltrade/                    # Django project settings
│   ├── __init__.py                # Celery app initialization
│   ├── settings.py                # Django settings with Channels & Redis
│   ├── urls.py                    # Main URL configuration
│   ├── asgi.py                    # ASGI application with WebSocket routing
│   ├── wsgi.py                    # WSGI application
│   └── celery.py                  # Celery configuration & beat schedule
│
├── trading/                        # Core trading application
│   ├── __init__.py
│   ├── models.py                  # Trade, TradingSession, MarketSignal models
│   ├── views.py                   # API views for trading operations
│   ├── serializers.py             # DRF serializers
│   ├── urls.py                    # Trading URL patterns
│   ├── admin.py                   # Django admin configuration
│   ├── apps.py                    # App configuration
│   ├── consumers.py               # WebSocket consumers for real-time data
│   ├── routing.py                 # WebSocket URL routing
│   └── tasks.py                   # Celery tasks (auto-login, heartbeat)
│
├── market_data/                    # Market data management
│   ├── __init__.py
│   ├── models.py                  # OHLCV model
│   ├── views.py                   # Market data API views
│   ├── urls.py                    # Market data URLs
│   ├── admin.py                   # Admin configuration
│   ├── apps.py                    # App configuration
│   ├── binance_client.py          # Binance API wrapper
│   └── shoonya_client.py          # Shoonya API wrapper
│
├── users/                          # User management
│   ├── __init__.py
│   ├── models.py                  # UserProfile model
│   ├── views.py                   # User API views
│   ├── urls.py                    # User URLs
│   ├── admin.py                   # Admin configuration
│   └── apps.py                    # App configuration
│
├── risk_management/                # Risk management system
│   ├── __init__.py
│   ├── models.py                  # Risk models
│   ├── apps.py                    # App configuration
│   ├── slippage.py                # Slippage control logic
│   └── risk_manager.py            # Risk validation & management
│
├── scripts/                        # Deployment & utility scripts
│   ├── start_server.sh            # Gunicorn/Uvicorn startup script
│   ├── setup.sh                   # Initial setup script
│   ├── celery_worker.sh           # Celery worker startup
│   └── celery_beat.sh             # Celery beat startup
│
├── nginx/                          # Nginx configuration
│   └── nginx.conf                 # Production Nginx config with WebSocket
│
├── logs/                           # Application logs (created at runtime)
│
├── staticfiles/                    # Collected static files (created at runtime)
│
├── media/                          # User uploaded files (created at runtime)
│
├── Dockerfile                      # Docker image definition
├── docker-compose.yml              # Multi-container orchestration
├── requirements.txt                # Python dependencies
├── manage.py                       # Django management script
├── .env.example                    # Environment variables template
├── .gitignore                      # Git ignore rules
│
├── README.md                       # Project overview & quick start
├── DEPLOYMENT.md                   # Deployment guide
├── API_DOCUMENTATION.md            # API reference
├── ARCHITECTURE.md                 # System architecture details
└── PROJECT_STRUCTURE.md            # This file
```

## Key Files Explained

### Configuration Files

- **settings.py**: Django settings with Channels, Redis, Celery, and trading configuration
- **asgi.py**: ASGI application with WebSocket routing for real-time connections
- **celery.py**: Celery configuration with beat schedule for automated tasks
- **.env.example**: Template for environment variables (API keys, credentials)

### Trading Core

- **trading/models.py**: Database models for trades, sessions, and signals
- **trading/consumers.py**: Async WebSocket consumer for Binance streaming
- **trading/tasks.py**: Celery tasks for auto-login, token refresh, and monitoring
- **trading/views.py**: REST API endpoints for trading operations

### Market Data

- **market_data/consumers.py**: Real-time market data streaming
- **market_data/binance_client.py**: Binance API integration
- **market_data/shoonya_client.py**: Shoonya/Finvasia API integration

### Risk Management

- **risk_management/slippage.py**: Slippage calculation and control
- **risk_management/risk_manager.py**: Trade validation and risk checks

### Deployment

- **Dockerfile**: Python 3.11 image with all dependencies
- **docker-compose.yml**: Services: Django, Celery, Redis, PostgreSQL, Nginx
- **nginx/nginx.conf**: Reverse proxy with WebSocket support
- **scripts/**: Shell scripts for starting services

## Docker Services

1. **db**: TimescaleDB (PostgreSQL 15 with time-series extension)
2. **redis**: Redis 7 with persistence
3. **django**: Django/Channels ASGI application
4. **celery_worker**: Celery worker for background tasks
5. **celery_beat**: Celery beat scheduler
6. **nginx**: Nginx reverse proxy

## Redis Key Patterns

```
auth:binance:token              # Binance session token (6h expiry)
auth:shoonya:token              # Shoonya session token (24h expiry)
market:data:{symbol}            # Current market data cache
market:ticks:{symbol}           # List of recent ticks (10k max)
market:heartbeat                # Last heartbeat timestamp
trades:active                   # Set of active trade IDs
trades:count:{date}             # Daily trade counter
trade:{id}                      # Individual trade data hash
```

## API Endpoints

```
/api/trading/status/            # System health check
/api/trading/trades/            # Trade CRUD operations
/api/trading/signals/           # AI-generated signals
/api/market/ohlcv/{symbol}/     # OHLCV candlestick data
/api/users/profile/             # User profile
/ws/market/{symbol}/            # WebSocket for real-time data
```

## Celery Tasks

```
auto_login_shoonya              # Daily at 8:45 AM
refresh_binance_token           # Every 6 hours
market_watch_heartbeat          # Every 1 second
cleanup_expired_tokens          # Daily at midnight
monitor_trade                   # On-demand per trade
execute_exit                    # On-demand for exits
```

## Environment Variables

See `.env.example` for complete list:
- Django settings (SECRET_KEY, DEBUG, ALLOWED_HOSTS)
- Database credentials
- Redis configuration
- Binance API keys
- Shoonya credentials & TOTP secret
- Trading parameters (slippage thresholds, max trades)

## Getting Started

1. Copy `.env.example` to `.env` and configure
2. Run `./scripts/setup.sh` or `docker-compose up --build`
3. Access at http://localhost
4. Admin panel: http://localhost/admin (admin/admin123)
5. API docs: See API_DOCUMENTATION.md
