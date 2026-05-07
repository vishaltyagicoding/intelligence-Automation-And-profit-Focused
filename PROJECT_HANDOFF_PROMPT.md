# NeuralTrade Project - AI Agent Handoff Instructions

## PROJECT OVERVIEW
This is a **production-ready cryptocurrency trading platform** called **NeuralTrade**. It's a full-stack application with:
- **Backend**: Django + PostgreSQL + Redis + Celery + WebSockets
- **Frontend**: Next.js 14 + TypeScript + TailwindCSS + lightweight-charts
- **Deployment**: Docker Compose (ready for AWS deployment)

The project displays **real-time cryptocurrency charts** with live price feeds from Binance via WebSocket.

---

## CURRENT STATE (AS OF NOW)

### ✅ What's Working
1. **Docker containers running**: django, frontend, nginx, redis, db, celery_worker, celery_beat
2. **Frontend accessible** at `http://localhost` (port 80 via nginx)
3. **Navigation bar** with Home, About, Learn, History, Login, Sign Up
4. **Clean candlestick chart** with:
   - Live WebSocket price feed from Binance
   - Timeframe switching (1m, 3m, 5m, 10m, 15m, 30m, 1h, 2h, 4h, 1d)
   - "View Full Dashboard" button (centered, blue)
   - NO labels, NO markers, NO lines (clean chart only)
5. **Backend API** fully functional with reversal zone calculation logic preserved
6. **TradingView Pine Script logic** intact in `reversal_zones/reversal_calculator.py` (DO NOT MODIFY)

### 🚫 What Was Removed
- All BUY/SELL labels from chart
- All horizontal lines (green/red)
- All blue dashed connecting lines
- Chart blinking/flashing issue (was caused by markers loading before candles)

### 📁 Key Files
- `components/ChartComponent.tsx` - Main chart component (clean, no labels)
- `app/page.tsx` - Homepage with watchlist and chart
- `app/layout.tsx` - Navigation bar
- `reversal_zones/reversal_calculator.py` - **CRITICAL: Original Pine Script logic (DO NOT CHANGE)**
- `trading/views.py` - API endpoint for reversal zones (still works, just not displayed)
- `docker-compose.yml` - All services configuration
- `nginx/nginx.conf` - Routes `/` to frontend, `/api/` to backend

---

## USER'S REQUIREMENTS & CONSTRAINTS

### 🔴 CRITICAL RULES (NEVER BREAK THESE)
1. **"don't create fake migrations is production ready project"** - Don't create unnecessary Django migrations
2. **"don't create new frontend previous frontend already exists"** - Modify existing components, don't create new pages
3. **"fix all don't create mistake and error"** - User wants working solutions without errors
4. **"did you change treading veiw pin script logic please don't change"** - NEVER modify `reversal_zones/reversal_calculator.py` logic
5. **"this is production project i have to deploy this project tommaro"** - This is URGENT, needs to work perfectly
6. **"don't create those files again and again"** - Stop creating documentation files unless explicitly requested
7. **"when ever you go in new sesion instatuction shuold be same"** - Instructions persist across sessions

### 🎯 User's Expectations
- User is **extremely frustrated** with repeated failures
- User wants **immediate, working solutions** - no experiments
- User will **remove you from the project** if you fail again
- User needs this deployed **tomorrow** (production-ready)
- User speaks English as second language - be patient and clear

---

## WHAT TO DO NEXT

### Option 1: Deploy to AWS (User mentioned this)
The user wants to deploy this to AWS. Everything is ready:
1. **Files exist**: `docker-compose.prod.yml`, `deploy.sh`, `deploy.ps1`, `.env.production`
2. **Guide exists**: `AWS_DEPLOYMENT_GUIDE.md`
3. **What to do**:
   - Ask user if they have AWS account ready
   - Ask for AWS credentials (Access Key, Secret Key)
   - Ask which AWS region they prefer
   - Guide them through EC2 instance setup
   - Run deployment scripts

### Option 2: Add New Features to Chart
If user wants to add features back to the chart:
1. **Ask first** what specific feature they want
2. **Show example** of what it will look like
3. **Get approval** before implementing
4. **Test thoroughly** before showing to user

### Option 3: Fix Any Bugs
If user reports bugs:
1. **Read error messages carefully**
2. **Check Docker logs**: `docker-compose logs -f [service_name]`
3. **Test locally** before claiming it's fixed
4. **Don't guess** - verify the fix works

### Option 4: Integrate Different AI Agent for Labels
User mentioned: "i will use different ai agent" for labels. If user wants to integrate another AI:
1. Ask what AI service they want to use
2. Ask for API keys
3. Create new endpoint in `trading/views.py`
4. Keep reversal zone logic separate
5. Display AI signals separately from reversal zones

---

## COMMON ISSUES & SOLUTIONS

### Issue: "Chart is blinking/flashing"
**Cause**: Markers being set before candles finish rendering
**Solution**: Use `requestAnimationFrame` or wait for chart's `timeScale()` to stabilize before calling `setMarkers()`

### Issue: "Labels appearing on same candle"
**Cause**: Timestamps not matching candle times exactly
**Solution**: Snap timestamps to candle boundaries: `Math.floor(timestamp / candleInterval) * candleInterval`

### Issue: "WebSocket connection refused"
**Cause**: nginx not routing `/ws/` correctly or backend not running
**Solution**: Check `nginx/nginx.conf` has WebSocket upgrade headers, verify Django Channels is running

### Issue: "Frontend build fails"
**Cause**: TypeScript errors or missing dependencies
**Solution**: Run `getDiagnostics` tool first, fix errors, then rebuild

### Issue: "Backend crashes on startup"
**Cause**: Missing Python dependencies or database migration issues
**Solution**: Check `requirements.txt`, run `docker-compose logs django`, fix imports

---

## DOCKER COMMANDS (USER IS ON WINDOWS)

```bash
# Rebuild and restart everything
docker-compose build && docker-compose up -d

# Rebuild only frontend
docker-compose build frontend && docker-compose up -d frontend

# Rebuild only backend
docker-compose build django && docker-compose up -d django

# View logs
docker-compose logs -f django
docker-compose logs -f frontend
docker-compose logs -f nginx

# Stop everything
docker-compose down

# Stop and remove volumes (fresh start)
docker-compose down -v

# Check running containers
docker-compose ps
```

---

## TECH STACK DETAILS

### Backend
- **Django 4.2** with Django REST Framework
- **PostgreSQL** for database
- **Redis** for caching and Celery broker
- **Celery** for background tasks (token refresh, reversal zone calculation)
- **Django Channels** for WebSocket support
- **CCXT** for Binance API integration

### Frontend
- **Next.js 14** (App Router)
- **TypeScript**
- **TailwindCSS** for styling
- **lightweight-charts** for candlestick charts
- **WebSocket** for real-time price feed

### Infrastructure
- **Docker Compose** for local development
- **nginx** as reverse proxy
- **Gunicorn** for Django WSGI
- **Daphne** for Django ASGI (WebSockets)

---

## FILE STRUCTURE (IMPORTANT LOCATIONS)

```
/
├── app/                          # Next.js pages
│   ├── page.tsx                  # Homepage with chart
│   ├── layout.tsx                # Navigation bar
│   └── asset/[symbol]/page.tsx   # Full dashboard page
├── components/
│   ├── ChartComponent.tsx        # Main chart (CLEAN, NO LABELS)
│   └── Watchlist.tsx             # Asset selector sidebar
├── reversal_zones/               # Backend reversal zone app
│   ├── reversal_calculator.py    Pine Script logic
│   ├── models.py                 # Database models
│   ├── views.py                  # API endpoints
│   └── tasks.py                  # Celery tasks
├── trading/                      # Backend trading app
│   ├── views.py                  # Main API endpoints
│   ├── consumers.py              # WebSocket consumers
│   └── tasks.py                  # Celery tasks
├── nginx/
│   └── nginx.conf                # Reverse proxy config
├── docker-compose.yml            # Local development
├── docker-compose.prod.yml       # Production deployment
└── requirements.txt              # Python dependencies
```

---

## TESTING CHECKLIST

Before telling user "it's fixed":
1. ✅ Run `docker-compose build` - no errors?
2. ✅ Run `docker-compose up -d` - all containers running?
3. ✅ Open `http://localhost` - page loads?
4. ✅ Check browser console - no errors?
5. ✅ Check Docker logs - no crashes?
6. ✅ Test timeframe switching - works smoothly?
7. ✅ Test WebSocket - prices updating live?
8. ✅ Test navigation - all links work?

---

## COMMUNICATION STYLE WITH USER

### ✅ DO:
- Be direct and concise
- Show code changes clearly
- Test before claiming it works
- Admit if you don't know something
- Ask clarifying questions if unclear

### ❌ DON'T:
- Create documentation files unless asked
- Make assumptions about what user wants
- Claim something works without testing
- Change the Pine Script logic
- Create new pages when modifying existing ones
- Use overly technical jargon

---

## EMERGENCY RECOVERY

If everything breaks:
1. Stop all containers: `docker-compose down`
2. Remove volumes: `docker-compose down -v`
3. Rebuild from scratch: `docker-compose build --no-cache`
4. Start fresh: `docker-compose up -d`
5. Check logs: `docker-compose logs -f`

---

## FINAL NOTES

- User has been working on this for **3+ hours** trying to fix chart blinking
- User is **very frustrated** and will switch to another AI if you fail
- This is a **production project** that needs to be deployed **tomorrow**
- The **Pine Script logic is sacred** - never touch it
- User wants **clean, working code** - no experiments

**Your job**: Help the user deploy this to AWS or add new features they request. Be reliable, test thoroughly, and don't break what's working.

---

## NEXT IMMEDIATE STEPS

1. **Ask user**: "What would you like to do next? Deploy to AWS or add new features?"
2. **Wait for response** - don't assume
3. **Confirm understanding** before starting work
4. **Test everything** before showing results
5. **Be honest** if something doesn't work

Good luck! 🚀
