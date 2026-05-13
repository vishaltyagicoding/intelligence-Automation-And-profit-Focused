# SmartRisk - Complete Project Overview

## What is SmartRisk?

SmartRisk is a production-ready cryptocurrency trading signal platform that provides real-time BUY/SELL signals based on reversal zone analysis. The platform monitors Bitcoin, Ethereum, Gold (XAUUSD), and Litecoin across multiple timeframes (5m to 1d) and sends instant email alerts to subscribed users when new signals are detected.

## Key Features

### 1. Real-Time Signal Generation
- Analyzes price action every 15 minutes
- Detects reversal zones using proprietary algorithm
- Generates BUY/SELL signals with entry, stop loss, and target prices
- Anti-chop filter prevents noisy signals

### 2. Multi-Asset Support
- **BTCUSD** (Bitcoin)
- **ETHUSD** (Ethereum)
- **XAUUSD** (Gold - via PAXGUSDT)
- **LTCUSD** (Litecoin)

### 3. Multi-Timeframe Analysis
- 5m, 15m, 30m, 1h, 2h, 4h, 1d
- Default: 15m timeframe
- Each timeframe analyzed independently

### 4. Live Price Updates
- WebSocket connections for real-time prices
- Automatic fallback to REST API if WebSocket stale
- Instant price display on page load
- No polling delays

### 5. Interactive Charts
- TradingView-style candlestick charts
- Reversal zone overlays
- BUY/SELL signal markers
- Timeframe switching

### 6. Email Notifications
- Instant alerts when new signals fire
- Customizable per symbol and timeframe
- HTML email templates
- Only for activated users

### 7. Signal History
- Last 5 months of signals
- Live WebSocket updates (no page refresh)
- Filtering by symbol and action
- Parallel data loading for speed

### 8. User Management
- Registration with email verification
- 3-day free trial
- Manual subscription activation by admin
- Protected routes

## Technical Architecture

### Frontend
- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: TailwindCSS
- **Charts**: Lightweight Charts (TradingView)
- **State**: React Context API
- **Real-time**: WebSocket

### Backend
- **Framework**: Django 5.0
- **API**: Django REST Framework
- **WebSocket**: Django Channels
- **Task Queue**: Celery + Redis
- **Database**: PostgreSQL 16
- **Data Source**: Binance.US API

### Infrastructure
- **Hosting**: AWS EC2 (us-west-1)
- **Web Server**: Nginx (reverse proxy + SSL)
- **Containerization**: Docker + Docker Compose
- **CI/CD**: GitHub Actions
- **SSL**: Let's Encrypt (auto-renewal)
- **Domain**: smartriskfx.com

## Signal Calculation Logic

### Reversal Zone Detection
1. Fetch OHLCV data from Binance.US
2. Calculate reversal zones using proprietary algorithm
3. Identify core and outer zone boundaries
4. Determine BUY (bullish) or SELL (bearish) signal

### Entry, Stop Loss, Target Calculation

**For BUY signals:**
```
entry = center_price (reversal zone center)
target = outer_top (upper boundary)
calculate = target - entry
stoploss = entry - (calculate * 0.5)
```

Example: entry=$50,000, target=$52,000 → stoploss=$49,000

**For SELL signals:**
```
entry = center_price (reversal zone center)
target = outer_bottom (lower boundary)
calculate = entry - target
stoploss = target + (calculate * 0.5)
```

Example: entry=$52,000, target=$50,000 → stoploss=$53,000

### Anti-Chop Filter
- **Minimum 1-hour gap** between any two signals
- **Strict alternation**: BUY → SELL → BUY → SELL
- Prevents clustered/noisy signals
- Ensures quality over quantity

## Data Flow

### 1. Price Data Collection
```
Binance.US API → Django Backend → WebSocket → Frontend
                      ↓
                 PostgreSQL (historical)
```

### 2. Signal Generation
```
Celery Beat (every 15 min) → Reversal Calculator → Anti-Chop Filter
                                                          ↓
                                                    PostgreSQL
                                                          ↓
                                                    Email Alerts
                                                          ↓
                                                    WebSocket Broadcast
```

### 3. User Interaction
```
User → Frontend → Nginx → Django API → PostgreSQL
                    ↓
              WebSocket → Django Channels → Redis
```

## User Journey

### 1. Registration
- User signs up with email and password
- Email verification sent
- 3-day trial activated automatically

### 2. Dashboard Access
- Login with credentials
- View live prices for all assets
- Interactive charts with reversal zones
- Switch between timeframes

### 3. Signal Alerts Setup
- Navigate to Signal Alerts page
- Select symbols and timeframes to monitor
- Enable email notifications
- Test email functionality

### 4. Receiving Signals
- New signal fires every 15 minutes (if conditions met)
- Email sent instantly to activated users
- Signal appears in history page immediately
- Chart updates with new reversal zone

### 5. Signal History
- View last 5 months of signals
- Filter by symbol (BTCUSD, ETHUSD, etc.)
- Filter by action (BUY, SELL, ALL)
- Live updates via WebSocket

### 6. Subscription Management
- Trial ends after 3 days
- Admin manually activates subscription
- Deactivated users redirected to subscription page

## Admin Operations

### Admin Accounts
- **alberttyagi123@gmail.com** (password: SmartRisk@2026!)
- **pythonbyvishal@gmail.com** (password: SmartRisk@2026!)

### Admin Tasks
1. **Activate User Subscription**
   - Login to Django admin
   - Find user's profile
   - Set `manual_subscription` to "activated"

2. **Monitor System Health**
   - Check logs: `sudo docker-compose logs -f`
   - View system status: `/api/trading/system-status/`
   - Monitor Celery tasks

3. **Database Management**
   - Run migrations
   - Create backups
   - View signal history

## Deployment

### Production Server
- **IP**: 54.183.178.141
- **SSH**: `ssh -i smartriskfx1.pem ubuntu@54.183.178.141`
- **Project Path**: `~/smartrisk`

### Deployment Process
1. Push code to `main` branch on GitHub
2. GitHub Actions triggers automatically
3. SSH into EC2 server
4. Pull latest code
5. Rebuild Docker containers
6. Run migrations
7. Collect static files
8. Health check

### Manual Deployment
```bash
ssh -i smartriskfx1.pem ubuntu@54.183.178.141
cd ~/smartrisk
git pull origin main
sudo docker-compose down
sudo docker-compose up -d --build
sudo docker-compose exec django python manage.py migrate
```

## Important Configuration

### Environment Files
- **Production Backend**: `.env` (NOT .env.production)
- **Production Frontend**: `.env` (NOT .env.local)
- **Docker Compose**: `docker-compose.yml` (NOT docker-compose.prod.yml)

### Container Names
- Database: `db`
- Redis: `redis`
- Backend: `django` (NOT "backend")
- Frontend: `frontend`
- Nginx: `nginx`

### API URLs
- **Frontend → Backend**: `http://django:8000` (internal Docker network)
- **External**: `https://smartriskfx.com/api`
- **WebSocket**: `wss://smartriskfx.com/ws`

### Token Name
- **Correct**: `access_token`
- **Incorrect**: `auth_token`

## Common Issues and Solutions

### 1. Prices Not Updating
- **Cause**: WebSocket connection stale
- **Solution**: Hybrid WebSocket + REST API fallback implemented
- **Location**: `trading/consumers.py`

### 2. Login Not Working
- **Cause**: Token name mismatch or CORS issue
- **Solution**: Use `access_token`, check CORS settings
- **Location**: `lib/AuthContext.tsx`, `neuraltrade/settings.py`

### 3. Signals Not Generating
- **Cause**: Celery worker not running
- **Solution**: Check Celery logs, restart django container
- **Command**: `sudo docker-compose logs django | grep celery`

### 4. Email Not Sending
- **Cause**: Gmail app password incorrect
- **Solution**: Generate new app password, update .env
- **Location**: `.env` → `EMAIL_HOST_PASSWORD`

### 5. Binance API Error
- **Cause**: Using api.binance.com instead of api.binance.us
- **Solution**: All API calls use `api.binance.us` with `tld='us'`
- **Location**: Multiple files (see context transfer)

## Project Statistics

### Codebase
- **Backend**: ~15 Django apps
- **Frontend**: ~20 pages and components
- **Database**: 10+ models
- **API Endpoints**: 20+ endpoints
- **WebSocket Consumers**: 1 main consumer
- **Celery Tasks**: 5+ periodic tasks

### Performance
- **Signal Generation**: Every 15 minutes
- **WebSocket Latency**: <100ms
- **API Response Time**: <500ms
- **Chart Load Time**: <2 seconds
- **Email Delivery**: <5 seconds

### Scale
- **Supported Assets**: 4 cryptocurrencies
- **Timeframes**: 7 timeframes
- **Total Combinations**: 28 symbol+timeframe pairs
- **Historical Data**: 5 months
- **Concurrent Users**: 100+ (current capacity)

## Future Enhancements

### Planned Features
- [ ] More cryptocurrencies (SOL, ADA, DOT)
- [ ] SMS notifications
- [ ] Mobile app (React Native)
- [ ] Advanced charting tools
- [ ] Backtesting functionality
- [ ] Performance analytics
- [ ] Social trading features
- [ ] API for third-party integrations

### Infrastructure Improvements
- [ ] CDN for static assets
- [ ] Database read replicas
- [ ] Redis cluster
- [ ] Load balancer
- [ ] Auto-scaling
- [ ] Monitoring dashboard (Grafana)
- [ ] Log aggregation (ELK stack)

## Documentation Structure

All project documentation is organized in `.claude/` directory:

```
.claude/
├── CLAUDE.md                    # This overview
├── rules/
│   ├── code-style.md           # Coding standards
│   ├── api-conventions.md      # API design patterns
│   ├── database.md             # Database schema
│   ├── frontend.md             # Frontend architecture
│   ├── deployment.md           # Deployment guide
│   └── testing.md              # Testing guidelines
├── commands/
│   ├── build.md                # Build commands
│   ├── deploy.md               # Deployment commands
│   ├── fix-issue.md            # Troubleshooting
│   └── review.md               # Code review process
└── skills/
    ├── backend/SKILL.md        # Backend development
    ├── frontend/SKILL.md       # Frontend development
    └── deploy/SKILL.md         # Deployment operations
```

## Contact Information

### Support
- **Email**: smarttriskfx@gmail.com
- **Admin**: alberttyagi123@gmail.com

### Repository
- **GitHub**: https://github.com/vishaltyagicoding/intelligence-Automation-And-profit-Focused

### Server
- **IP**: 54.183.178.141
- **Domain**: smartriskfx.com

---

**Last Updated**: May 11, 2026
**Version**: 1.0.0
**Status**: Production Ready
