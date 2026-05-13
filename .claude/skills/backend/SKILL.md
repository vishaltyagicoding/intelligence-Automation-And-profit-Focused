# Backend Development Skill

## Overview
Django REST Framework backend with WebSocket support, Celery task queue, and PostgreSQL database.

## Core Technologies
- Django 5.0
- Django REST Framework
- Django Channels (WebSocket)
- Celery + Redis
- PostgreSQL 16
- Binance.US API

## Key Components

### API Endpoints (`trading/views.py`)
- Reversal zone data retrieval
- Signal history with filtering
- System health checks
- WebSocket connection management

### WebSocket Consumers (`trading/consumers.py`)
- Real-time price updates
- Signal broadcasting
- Hybrid WebSocket + REST fallback
- Connection lifecycle management

### Celery Tasks (`reversal_zones/tasks.py`)
- Signal calculation every 15 minutes
- Email notifications for activated users
- Historical data backfill
- Anti-chop filtering

### Models
- `ReversalZone`: Stores calculated reversal zones
- `SignalAlert`: User alert preferences
- `Trade`: User trade history
- `MarketSignal`: Generated signals
- `UserProfile`: Extended user data

## Signal Calculation Logic

### Formula
**For BUY signals:**
```python
entry = center_price
target = outer_top
calculate = target - entry
stoploss = entry - (calculate * 0.5)
```

**For SELL signals:**
```python
entry = center_price
target = outer_bottom
calculate = entry - target
stoploss = target + (calculate * 0.5)
```

### Anti-Chop Filter
- Minimum 1-hour gap between signals
- Strict alternation: BUY → SELL → BUY
- Prevents noisy/clustered signals

## WebSocket Protocol

### Connection URL
```
wss://smartriskfx.com/ws/market/<symbol>/<timeframe>/
```

### Message Types
1. **kline**: Price update
2. **signal**: New BUY/SELL signal
3. **connection**: Status message

### Fallback Mechanism
- If same price received 3x → fetch from REST API
- If no update for 30s → fetch from REST API
- Ensures prices always update

## Email Notifications

### Configuration
- SMTP: Gmail (smtp.gmail.com:587)
- From: smarttriskfx@gmail.com
- Template: HTML with signal details

### Trigger
- New signal generated
- User has alert enabled for symbol+timeframe
- User subscription is active

## Database Optimization

### Indexes
```python
class Meta:
    indexes = [
        models.Index(fields=['symbol', 'timeframe', '-reversal_time']),
        models.Index(fields=['symbol', 'is_bullish']),
    ]
    unique_together = [['symbol', 'timeframe', 'reversal_time']]
```

### Query Optimization
- Use `select_related()` for ForeignKey
- Use `prefetch_related()` for reverse relations
- Cache frequently accessed data in Redis

## Celery Configuration

### Beat Schedule
```python
CELERY_BEAT_SCHEDULE = {
    'check-reversal-signals': {
        'task': 'reversal_zones.tasks.check_reversal_signals',
        'schedule': crontab(minute='*/15'),  # Every 15 minutes
    },
}
```

### Task Best Practices
- Make tasks idempotent
- Add retry logic with exponential backoff
- Log task execution
- Handle exceptions gracefully

## API Response Format

### Success
```json
{
  "success": true,
  "data": { ... }
}
```

### Error
```json
{
  "success": false,
  "error": "Error message"
}
```

## Authentication
- Token-based (DRF TokenAuthentication)
- Token name: `access_token`
- Header: `Authorization: Bearer <token>`

## Common Tasks

### Add New API Endpoint
1. Define view in `views.py`
2. Add URL pattern in `urls.py`
3. Add permissions if needed
4. Test with curl/Postman

### Add Celery Task
1. Define task in `tasks.py`
2. Add to beat schedule if periodic
3. Test with `.delay()` or `.apply_async()`

### Add WebSocket Event
1. Update consumer in `consumers.py`
2. Add message type handling
3. Update frontend to handle new event

## Debugging

### View Logs
```bash
sudo docker-compose logs -f django
```

### Django Shell
```bash
sudo docker-compose exec django python manage.py shell
```

### Test Celery Task
```bash
sudo docker-compose exec django python manage.py shell
>>> from reversal_zones.tasks import check_reversal_signals
>>> check_reversal_signals.delay()
```

## Performance Tips
- Use database connection pooling
- Cache API responses in Redis
- Optimize database queries
- Use async views for I/O operations
- Implement rate limiting
