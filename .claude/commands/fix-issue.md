# Common Issues and Fixes

## Authentication Issues

### Login Not Working
```bash
# Check backend logs
sudo docker-compose logs django | grep -i "login\|auth"

# Verify token generation
sudo docker-compose exec django python manage.py shell
>>> from rest_framework.authtoken.models import Token
>>> Token.objects.all()

# Check CORS settings
# Ensure ALLOWED_HOSTS includes domain in settings.py
```

### Token Name Mismatch
- Frontend uses `access_token` (NOT `auth_token`)
- Check localStorage in browser DevTools
- Update AuthContext if needed

## WebSocket Issues

### Prices Not Updating
```bash
# Check WebSocket connection in browser console
const ws = new WebSocket('wss://smartriskfx.com/ws/market/BTCUSD/15m/');
ws.onmessage = (e) => console.log(e.data);

# Check Django Channels logs
sudo docker-compose logs django | grep -i "websocket\|channel"

# Verify Redis connection
sudo docker-compose exec redis redis-cli ping
```

### Stale Price Data
- Implemented hybrid WebSocket + REST API fallback
- If same price 3x → fetch from REST API
- If timeout 30s → fetch from REST API
- Check `trading/consumers.py` for fallback logic

### WebSocket Disconnecting
```bash
# Check nginx WebSocket config
sudo docker-compose exec nginx cat /etc/nginx/nginx.conf | grep -A 10 "location /ws"

# Verify proxy settings
proxy_http_version 1.1;
proxy_set_header Upgrade $http_upgrade;
proxy_set_header Connection "upgrade";
```

## API Connection Issues

### Frontend Can't Reach Backend
```bash
# Check .env file
cat .env | grep API_URL

# Should be:
NEXT_PUBLIC_API_URL=http://django:8000  # Inside Docker
# NOT https://smartriskfx.com/api

# Verify nginx proxy
sudo docker-compose logs nginx | grep -i error
```

### 401 Unauthorized Errors
- Check token in localStorage
- Verify token format: `Bearer <token>`
- Check token expiration
- Ensure user is authenticated

### CORS Errors
```python
# In settings.py
CORS_ALLOWED_ORIGINS = [
    "https://smartriskfx.com",
    "http://localhost:3000",
]
```

## Database Issues

### Connection Refused
```bash
# Check database container
sudo docker-compose ps db

# Test connection
sudo docker-compose exec db pg_isready -U smartrisk_user -d neuraltrade

# Check credentials in .env
DB_NAME=neuraltrade
DB_USER=smartrisk_user
DB_HOST=db
```

### Migration Errors
```bash
# View migration status
sudo docker-compose exec django python manage.py showmigrations

# Fake migration if needed
sudo docker-compose exec django python manage.py migrate --fake app_name 0001

# Reset migrations (DANGER: loses data)
sudo docker-compose exec django python manage.py migrate app_name zero
```

### Database Warning: "database does not exist"
```bash
# Fix health check in docker-compose.yml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U ${DB_USER:-smartrisk_user} -d ${DB_NAME:-neuraltrade}"]
```

## Binance API Issues

### Geo-Restriction Error
- Use `api.binance.us` (NOT `api.binance.com`)
- Update all Binance API calls to use `.us` domain
- Set `tld='us'` in AsyncClient initialization

### Rate Limiting
```python
# Implement exponential backoff
import time
for attempt in range(3):
    try:
        response = await client.get_klines(...)
        break
    except Exception as e:
        if attempt < 2:
            time.sleep(2 ** attempt)
        else:
            raise
```

## Email Issues

### Emails Not Sending
```bash
# Check email settings in .env
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=smarttriskfx@gmail.com
EMAIL_HOST_PASSWORD=<app-password>  # NOT regular password

# Test email
sudo docker-compose exec django python manage.py shell
>>> from django.core.mail import send_mail
>>> send_mail('Test', 'Message', 'smarttriskfx@gmail.com', ['test@example.com'])
```

### Gmail App Password
1. Enable 2FA on Gmail account
2. Generate App Password: https://myaccount.google.com/apppasswords
3. Use App Password in EMAIL_HOST_PASSWORD

## SSL Certificate Issues

### Certificate Expired
```bash
# Check expiry
sudo certbot certificates

# Renew
sudo certbot renew
sudo docker-compose restart nginx
```

### Certificate Not Found
```bash
# Verify certificate location
ls -la /etc/letsencrypt/live/smartriskfx.com/

# Should contain:
# - fullchain.pem
# - privkey.pem
```

## Performance Issues

### Slow API Responses
```bash
# Check database query performance
sudo docker-compose exec django python manage.py shell
>>> from django.db import connection
>>> connection.queries  # View recent queries

# Add database indexes
# Check models.py for missing indexes
```

### High Memory Usage
```bash
# Check container stats
sudo docker stats

# Restart containers
sudo docker-compose restart

# Increase container limits in docker-compose.yml
```

### Slow Chart Loading
- Implement loading overlay
- Fetch initial price via REST API
- Use WebSocket for updates only
- Limit historical data to 500-1000 candles

## Docker Issues

### Container Won't Start
```bash
# Check logs
sudo docker-compose logs <service>

# Rebuild from scratch
sudo docker-compose down -v
sudo docker-compose up -d --build
```

### Port Already in Use
```bash
# Find process using port
sudo lsof -i :8000
sudo lsof -i :3000

# Kill process
sudo kill -9 <PID>
```

### Disk Space Full
```bash
# Check disk usage
df -h

# Clean Docker
sudo docker system prune -a

# Remove old logs
sudo journalctl --vacuum-time=7d
```

## Signal Calculation Issues

### Entry, Stop Loss, Target Same Value
**FIXED**: Use correct formula in `reversal_zones/tasks.py`

For BUY:
```python
target = outer_top
calculate = target - entry
stoploss = entry - (calculate * 0.5)
```

For SELL:
```python
target = outer_bottom
calculate = entry - target
stoploss = target + (calculate * 0.5)
```

### Signals Not Generating
```bash
# Check Celery worker
sudo docker-compose logs django | grep -i celery

# Manually trigger
sudo docker-compose exec django python manage.py shell
>>> from reversal_zones.tasks import check_reversal_signals
>>> check_reversal_signals.delay()
```

## Debugging Tools

### Django Shell
```bash
sudo docker-compose exec django python manage.py shell
```

### Database Shell
```bash
sudo docker-compose exec db psql -U smartrisk_user neuraltrade
```

### Redis CLI
```bash
sudo docker-compose exec redis redis-cli
```

### View Environment Variables
```bash
sudo docker-compose exec django env | grep -i db
```

## Emergency Contacts
- **Admin**: alberttyagi123@gmail.com
- **Support**: smarttriskfx@gmail.com
- **Server**: 54.183.178.141
