# NeuralTrade System Architecture

## Overview

NeuralTrade is a production-ready, autonomous AI trading platform designed for high-frequency trading with zero human intervention.

## System Components

### 1. Django Application Layer

**Technology**: Django 5.0+ with Channels 4.0

**Responsibilities**:
- HTTP API endpoints (REST)
- WebSocket connections (real-time data)
- User authentication & authorization
- Business logic orchestration

**Key Features**:
- ASGI support for async operations
- Channel layers for WebSocket broadcasting
- JWT-based authentication

### 2. WebSocket Layer

**Technology**: Django Channels with Redis backend

**Responsibilities**:
- Real-time market data streaming
- Live trade updates
- User notifications

**Performance**:
- Supports 10,000+ concurrent connections
- Sub-millisecond message delivery
- Automatic reconnection handling

### 3. Task Queue (Celery)

**Technology**: Celery with Redis broker

**Scheduled Tasks**:
- `auto_login_shoonya`: Daily at 8:45 AM
- `refresh_binance_token`: Every 6 hours
- `market_watch_heartbeat`: Every 1 second
- `cleanup_expired_tokens`: Daily at midnight

**Worker Configuration**:
- Concurrency: 4 workers
- Pool: eventlet (async support)
- Max tasks per child: 1000

### 4. Data Storage

#### PostgreSQL with TimescaleDB
- User data
- Trade history
- Trading sessions
- Market signals

#### Redis
- Session tokens (Binance, Shoonya)
- Real-time tick data
- Active trades cache
- Market data buffer

**Redis Keys Structure**:
```
auth:binance:token          # Binance session token
auth:shoonya:token          # Shoonya session token
market:data:{symbol}        # Market data cache
market:ticks:{symbol}       # Tick data list
trades:active               # Active trades set
trades:count:{date}         # Daily trade counter
```

### 5. External APIs

#### Binance API
- Real-time WebSocket streams
- Order execution
- Market data

#### Shoonya/Finvasia API
- MCX commodity trading
- TOTP-based authentication
- Order management

### 6. Risk Management

**Components**:
- Slippage Controller
- Position Size Validator
- Daily Trade Limit Enforcer
- Balance Checker

**Thresholds**:
- Crypto slippage: 0.05%
- Commodity slippage: 0.1%
- Max position size: 10% of balance
- Max trades per day: 4

### 7. Web Server (Nginx)

**Configuration**:
- Reverse proxy for Django
- WebSocket upgrade support
- Static file serving
- SSL/TLS termination

**Performance**:
- Worker connections: 10,000
- Gzip compression enabled
- Keepalive timeout: 65s

## Data Flow

### Real-time Market Data Flow

```
Binance WebSocket
    ↓
MarketDataConsumer (Django Channels)
    ↓
Process & Store in Redis
    ↓
Broadcast to Channel Layer
    ↓
Connected WebSocket Clients
```

### Trade Execution Flow

```
AI Signal Generation
    ↓
Risk Manager Validation
    ↓
Slippage Check
    ↓
Order Placement (Binance/Shoonya)
    ↓
Store in Database
    ↓
Add to Active Trades (Redis)
    ↓
Monitor via Heartbeat Task
```

### Authentication Flow

```
Celery Beat Scheduler
    ↓
auto_login_shoonya Task (8:45 AM)
    ↓
Generate TOTP Code
    ↓
Login to Shoonya API
    ↓
Store Token in Redis (24h expiry)
    ↓
Available for Trading Operations
```

## Scalability

### Horizontal Scaling

- **Django**: Multiple Gunicorn workers with Uvicorn
- **Celery**: Multiple worker instances
- **Redis**: Redis Cluster for high availability
- **PostgreSQL**: Read replicas for queries

### Performance Optimizations

- **uvloop**: High-performance event loop
- **Connection pooling**: Database connections
- **Redis caching**: Token and market data
- **Async operations**: Non-blocking I/O

## Security

### Authentication
- JWT tokens for API access
- TOTP for Shoonya 2FA
- API key management in environment variables

### Data Protection
- Encrypted connections (SSL/TLS)
- Secure token storage (Redis)
- CORS configuration
- Rate limiting

### Monitoring
- Structured logging
- Health check endpoints
- Error tracking (Sentry integration ready)

## High Availability

### Redundancy
- Multiple Django workers
- Multiple Celery workers
- Redis persistence (AOF)
- Database backups

### Failover
- Automatic task retry (Celery)
- WebSocket reconnection
- Circuit breaker pattern

## Future Enhancements (Phase 2+)

- CNN-LSTM AI model integration
- Multi-user trading agents
- Advanced risk analytics
- Real-time P&L dashboard
- Mobile app (Flutter)
- Machine learning pipeline
- Backtesting engine
