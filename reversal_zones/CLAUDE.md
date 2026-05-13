# Reversal Zones App Documentation

## Overview
The `reversal_zones` app handles the core signal generation logic: calculating reversal zones, applying anti-chop filters, sending email notifications, and storing signals in the database.

## App Structure
```
reversal_zones/
├── __init__.py
├── models.py                    # ReversalZone, ReversalStatus models
├── tasks.py                     # Celery tasks for signal generation
├── reversal_calculator.py       # Core reversal zone algorithm
├── signal_filter.py             # Anti-chop filter logic
├── admin.py                     # Django admin
└── management/
    └── commands/
        └── backfill_signals.py  # Historical data backfill
```

## Models

### ReversalZone
Stores calculated reversal zones permanently.

```python
class ReversalZone(models.Model):
    symbol = CharField(20)              # e.g., 'BTCUSDT'
    timeframe = CharField(10)           # e.g., '15m'
    reversal_time = DateTimeField       # When signal fired
    center_price = DecimalField(20, 8)  # Entry price
    outer_top = DecimalField(20, 8)     # Upper boundary
    outer_bottom = DecimalField(20, 8)  # Lower boundary
    core_top = DecimalField(20, 8)      # Core upper boundary
    core_bottom = DecimalField(20, 8)   # Core lower boundary
    is_bullish = BooleanField           # True=BUY, False=SELL
    label_text = CharField(10)          # 'BUY' or 'SELL'
    bar_index = IntegerField            # Chart bar index
    created_at = DateTimeField

    class Meta:
        unique_together = [['symbol', 'timeframe', 'reversal_time']]
        indexes = [
            Index(fields=['symbol', 'timeframe', '-reversal_time']),
            Index(fields=['symbol', 'is_bullish']),
        ]
```

### ReversalStatus
Tracks current signal state for each symbol.

```python
class ReversalStatus(models.Model):
    symbol = CharField(20, unique=True)
    last_signal = CharField(10)         # 'BUY', 'SELL', 'NONE'
    tracking = CharField(10)            # Current tracking state
    current_price = DecimalField(20, 8)
    updated_at = DateTimeField
```

## Signal Calculation Formula

### For BUY Signals
```python
entry = center_price
target = outer_top
calculate = target - entry
stoploss = entry - (calculate * 0.5)
```

**Example**:
- Entry: $50,000
- Target: $52,000
- Calculate: $52,000 - $50,000 = $2,000
- Stop Loss: $50,000 - ($2,000 × 0.5) = $49,000

### For SELL Signals
```python
entry = center_price
target = outer_bottom
calculate = entry - target
stoploss = target + (calculate * 0.5)
```

**Example**:
- Entry: $52,000
- Target: $50,000
- Calculate: $52,000 - $50,000 = $2,000
- Stop Loss: $50,000 + ($2,000 × 0.5) = $53,000

## Celery Tasks

### 1. check_reversal_signals
**Schedule**: Every 15 minutes

**Purpose**: Main signal generation task

**Process**:
1. Iterate through all symbols (BTCUSD, ETHUSD, XAUUSD, LTCUSD)
2. Iterate through all timeframes (5m, 15m, 30m, 1h, 2h, 4h, 1d)
3. Fetch OHLCV data from Binance.US
4. Calculate reversal zones
5. Apply anti-chop filter
6. Save new signals to database
7. Send email notifications
8. Broadcast via WebSocket

**Code Location**: `reversal_zones/tasks.py`

### 2. calculate_history_for_symbol_timeframe
**Trigger**: Manual or scheduled

**Purpose**: Backfill historical signals

**Parameters**:
- `symbol`: e.g., 'BTCUSD'
- `timeframe`: e.g., '15m'
- `days`: Number of days to backfill (default: 30)

**Process**:
1. Fetch historical OHLCV data
2. Calculate reversal zones for each candle
3. Apply anti-chop filter
4. Save to database (no emails sent)

### 3. calculate_all_history
**Trigger**: Manual

**Purpose**: Backfill all symbols and timeframes

**Process**:
- Queues `calculate_history_for_symbol_timeframe` for each combination
- Total: 4 symbols × 7 timeframes = 28 tasks

## Reversal Zone Calculator

### Algorithm Overview
Located in `reversal_zones/reversal_calculator.py`

**Input**: OHLCV DataFrame (pandas)

**Output**: List of reversal zones with:
- Center price (entry)
- Core boundaries (inner zone)
- Outer boundaries (outer zone)
- Is bullish (BUY/SELL)
- Bar index
- Timestamp

**Key Features**:
- Detects price reversals using proprietary algorithm
- Calculates zone boundaries based on volatility
- Identifies bullish (BUY) and bearish (SELL) zones
- Returns bar index for chart plotting

## Anti-Chop Filter

### Purpose
Prevents noisy, clustered signals that would confuse traders.

### Rules
1. **Minimum Time Gap**: 1 hour between ANY two signals
2. **Strict Alternation**: BUY → SELL → BUY → SELL (no consecutive same signals)

### Implementation
Located in `reversal_zones/signal_filter.py`

```python
class AntiChopFilter:
    def process(self, df, symbol, check_db=True, db_timestamps=None):
        # Calculate raw zones
        zones = self.calculator.calculate(df)
        
        # Apply time gap filter
        filtered = []
        last_time = None
        for zone in zones:
            if last_time and (zone.time - last_time) < 1_hour:
                continue  # Skip - too soon
            filtered.append(zone)
            last_time = zone.time
        
        # Apply alternation filter
        final = []
        last_signal = None
        for zone in filtered:
            if last_signal and zone.signal == last_signal:
                continue  # Skip - same as last
            final.append(zone)
            last_signal = zone.signal
        
        return final
```

### Database Check
Before saving new signal, checks if timestamp already exists in database to prevent duplicates.

## Email Notifications

### Configuration
- **SMTP**: Gmail (smtp.gmail.com:587)
- **From**: smarttriskfx@gmail.com
- **Template**: HTML with signal details

### Email Content
```
Subject: 🚨 New BUY Signal: BTCUSD (15m)

Body:
- Symbol: BTCUSD
- Timeframe: 15m
- Action: BUY
- Entry Price: $50,000.00
- Stop Loss: $49,000.00
- Target: $52,000.00
- Time: 2026-05-11 12:00:00 UTC
```

### Sending Logic
Located in `reversal_zones/tasks.py` → `_send_signal_notifications()`

**Process**:
1. Get all users with active subscriptions
2. Filter users with alerts enabled for this symbol+timeframe
3. Calculate entry, stop loss, target using formula
4. Send HTML email to each user
5. Log success/failure

**Code**:
```python
def _send_signal_notifications(zone, symbol, timeframe):
    from signal_alerts.models import SignalAlert
    from users.models import UserProfile
    
    # Get activated users with alerts
    alerts = SignalAlert.objects.filter(
        symbol=symbol,
        timeframe=timeframe,
        is_active=True,
        email_enabled=True,
        user__userprofile__manual_subscription='activated'
    )
    
    for alert in alerts:
        # Calculate prices
        entry = float(zone.center_price)
        if zone.is_bullish:
            target = float(zone.outer_top)
            calculate = target - entry
            stoploss = entry - (calculate * 0.5)
        else:
            target = float(zone.outer_bottom)
            calculate = entry - target
            stoploss = target + (calculate * 0.5)
        
        # Send email
        send_mail(
            subject=f"🚨 New {zone.label_text} Signal: {symbol} ({timeframe})",
            message=f"Entry: ${entry:.2f}\nStop Loss: ${stoploss:.2f}\nTarget: ${target:.2f}",
            from_email='smarttriskfx@gmail.com',
            recipient_list=[alert.user.email],
            html_message=render_html_template(...)
        )
```

## WebSocket Broadcasting

### Purpose
Notify frontend clients immediately when new signal fires.

### Implementation
```python
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

channel_layer = get_channel_layer()
async_to_sync(channel_layer.group_send)(
    f"market_{symbol}_{timeframe}",
    {
        "type": "signal_alert",
        "data": {
            "type": "signal",
            "asset": symbol,
            "timeframe": timeframe,
            "is_bullish": zone.is_bullish,
            "price": float(zone.center_price),
            "stop_loss": stoploss,
            "target": target,
            "timestamp": zone.reversal_time.isoformat(),
        }
    }
)
```

## Data Retention

### Policy
Keep last 5 months (150 days) of signals.

### Cleanup
```python
from django.utils import timezone
import datetime

cutoff = timezone.now() - datetime.timedelta(days=150)
ReversalZone.objects.filter(reversal_time__lt=cutoff).delete()
```

## Testing

### Test Signal Generation
```bash
sudo docker-compose exec django python manage.py shell
>>> from reversal_zones.tasks import check_reversal_signals
>>> check_reversal_signals.delay()
```

### Test Email Notification
```bash
sudo docker-compose exec django python manage.py test_live_signal_email
```

### Test Historical Backfill
```bash
sudo docker-compose exec django python manage.py shell
>>> from reversal_zones.tasks import calculate_history_for_symbol_timeframe
>>> calculate_history_for_symbol_timeframe.delay('BTCUSD', '15m', days=30)
```

## Common Issues

### 1. Signals Not Generating
**Cause**: Celery worker not running
**Solution**:
```bash
sudo docker-compose logs django | grep celery
sudo docker-compose restart django
```

### 2. Duplicate Signals
**Cause**: Anti-chop filter not working
**Solution**: Check database timestamp check in `signal_filter.py`

### 3. Emails Not Sending
**Cause**: Gmail app password incorrect
**Solution**: Generate new app password, update .env

### 4. Wrong Stop Loss/Target
**Cause**: Formula not applied correctly
**Solution**: Check `_send_signal_notifications()` in `tasks.py`

## Performance Optimization

### Database Queries
- Use `select_related()` for user/profile joins
- Add indexes on (symbol, timeframe, reversal_time)
- Batch insert signals

### Celery Tasks
- Use `apply_async()` for parallel execution
- Set task timeout to prevent hanging
- Implement retry logic with exponential backoff

### Caching
- Cache Binance API responses (60s)
- Cache reversal zone calculations (60s)
- Use Redis for fast lookups
