# SmartRisk - AI Trading Signal Platform

## Project Overview
SmartRisk is a production-ready cryptocurrency trading signal platform that provides real-time BUY/SELL signals based on reversal zone analysis. The platform monitors multiple cryptocurrencies across various timeframes and sends instant email alerts to subscribed users.

## Brand Information
- **Name**: SmartRisk (formerly NeuralTrade)
- **Contact Emails**: alberttyagi123@gmail.com, smarttriskfx@gmail.com
- **Domain**: smartriskfx.com
- **Protocol**: HTTPS with Let's Encrypt SSL certificates

## Tech Stack
- **Frontend**: Next.js 14 (App Router), TypeScript, TailwindCSS
- **Backend**: Django 5.0, Django REST Framework, Django Channels
- **Database**: PostgreSQL 16
- **Cache/Queue**: Redis, Celery
- **WebSocket**: Django Channels with Redis backend
- **Deployment**: Docker, Docker Compose, Nginx, AWS EC2 (us-west-1)
- **CI/CD**: GitHub Actions

## Key Features
1. Real-time price monitoring via WebSocket (Binance.US)
2. Reversal zone calculation and signal generation
3. Multi-timeframe analysis (5m, 15m, 30m, 1h, 2h, 4h, 1d)
4. Email alerts for activated users
5. User subscription management (3-day trial)
6. Signal history with live updates
7. Interactive TradingView-style charts

## Supported Assets
- BTCUSD (Bitcoin)
- ETHUSD (Ethereum)
- XAUUSD (Gold - mapped to PAXGUSDT)
- LTCUSD (Litecoin)

## Default Settings
- **Default Timeframe**: 15m
- **Signal Update Frequency**: Every 15 minutes
- **Trial Duration**: 3 days
- **Data Source**: Binance.US (api.binance.us)

## Admin Accounts
- alberttyagi123@gmail.com (password: SmartRisk@2026!)
- pythonbyvishal@gmail.com (password: SmartRisk@2026!)

## Production Server
- **IP**: 54.183.178.141
- **Region**: AWS us-west-1 (California)
- **Container Name**: "django" (not "backend")
- **Environment File**: `.env` (not .env.production)
- **Docker Compose**: `docker-compose.yml` (not docker-compose.prod.yml)


## Important Rules
1. **No temporary fixes** - Only production-ready, permanent solutions
2. **No ML dependencies** - Removed TensorFlow, PyTorch, scikit-learn
3. **Use Binance.US** - Not regular Binance (geo-restriction issue)
4. **HTTP for internal** - Frontend uses HTTP to connect to backend (nginx handles SSL)
5. **Token name**: `access_token` (not `auth_token`)
6. **Never commit** documentation files matching patterns: *_FIX_*, *_COMPLETE*, etc.

## Project Structure
See `.claude/` directory for detailed documentation on:
- Code style and conventions
- API endpoints and data models
- Database schema
- Deployment procedures
- Testing guidelines
