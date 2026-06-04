# Database Schema — Current State

## Connection
- Engine: PostgreSQL 16
- Host: `db` (Docker container)
- Port: 5432
- Name: `neuraltrade`
- User: `smartrisk_user`

## ReversalZone (core signal table)
```python
symbol          CharField(20)            # 'BTCUSDT' (Binance symbol, NOT 'BTCUSD')
timeframe       CharField(10)            # '5m','15m','30m','1h','2h','4h','1d'
reversal_time   DateTimeField            # PIVOT BAR timestamp — NEVER changes after insert
center_price    DecimalField(20,8)       # entry price (pivot raw price)
stop_loss       DecimalField(20,8,null)  # 1.0×ATR below/above entry (nullable: old records may be NULL)
target          DecimalField(20,8,null)  # 2.0×ATR above/below entry (nullable: old records may be NULL)
outer_top       DecimalField(20,8)       # = target for BUY, = stop_loss for SELL
outer_bottom    DecimalField(20,8)       # = stop_loss for BUY, = target for SELL
core_top        DecimalField(20,8)       # tight zone top (entry + core_half)
core_bottom     DecimalField(20,8)       # tight zone bottom (entry - core_half)
is_bullish      BooleanField             # True = BUY, False = SELL
label_text      CharField(10)           # 'BUY' or 'SELL'
bar_index       IntegerField            # SET ONCE on INSERT — never updated (relative position)
status          CharField(20,default='OPEN')  # 'OPEN','TARGET_HIT','SL_HIT'
created_at      DateTimeField(auto_now_add)

unique_together: ['symbol', 'timeframe', 'reversal_time']
ordering: ['-reversal_time']
```

### CRITICAL: bar_index Rule
`bar_index` is a relative offset in the data window at the time of detection.
It SHIFTS every time the calculator runs with a new window.
**Rule**: NEVER put `bar_index` in `update_or_create` defaults.
Set it once with `obj.bar_index = val; obj.save(update_fields=["bar_index"])` on `created=True` only.

### CRITICAL: stop_loss/target Nullable
Old signals in DB (before the ATR-based SL/Target update) have NULL stop_loss and target.
`views.py` handles this with fallback:
```python
explicit_sl  = float(rec.stop_loss) if rec.stop_loss else outer_bot_val if is_bull else outer_top_val
explicit_tgt = float(rec.target)    if rec.target    else outer_top_val if is_bull else outer_bot_val
```
To populate NULL records: run `python backfill_signals.py` on server.

## Other Models

### UserProfile
```python
user          OneToOneField(User)
trial_start   DateTimeField
trial_end     DateTimeField
manual_subscription  CharField(20)   # 'activated' or 'deactivated'
```

### SignalAlert
```python
user          ForeignKey(User)
symbol        CharField(20)
timeframe     CharField(10)
is_active     BooleanField
email_enabled BooleanField
unique_together: ['user', 'symbol', 'timeframe']
```

### MarketSignal
```python
symbol        CharField(20)
timeframe     CharField(10)
action        CharField(10)   # 'BUY' or 'SELL'
price         DecimalField
stop_loss     DecimalField
target        DecimalField
status        CharField(20)   # 'OPEN', 'CLOSED'
```

## Migrations
Location: `reversal_zones/migrations/`, `trading/migrations/`, etc.
```bash
sudo docker-compose exec django python manage.py migrate          # apply
sudo docker-compose exec django python manage.py makemigrations   # create new
sudo docker-compose exec django python manage.py showmigrations   # status
```

## Asset Symbol Mapping (frontend → Binance)
| Frontend Symbol | Binance Symbol | Note |
|---|---|---|
| BTCUSD | BTCUSDT | Standard |
| ETHUSD | ETHUSDT | Standard |
| XAUUSD | PAXGUSDT | Gold via PAX Gold token |
| LTCUSD | LTCUSDT | Standard |