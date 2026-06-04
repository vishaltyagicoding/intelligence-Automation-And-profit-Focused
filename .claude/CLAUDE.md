# SmartRisk — Algorithmic Crypto Trading Signal Platform

## Project Identity
- **Name**: SmartRisk (codebase/repo: intelligence-Automation-And-profit-Focused)
- **Domain**: https://smartriskfx.com
- **Purpose**: Real-time BUY/SELL reversal signals for crypto, with live chart, history page, email alerts
- **Contact**: alberttyagi123@gmail.com | smarttriskfx@gmail.com
- **Admin password**: SmartRisk@2026!
- **GitHub**: https://github.com/vishaltyagicoding/intelligence-Automation-And-profit-Focused

---

## Tech Stack
| Layer | Technology |
|---|---|
| Frontend | Next.js 14 App Router, TypeScript, TailwindCSS, Lightweight Charts v4.2.1 |
| Backend | Django 5.0, DRF, Django Channels (WebSocket) |
| DB | PostgreSQL 16 (name: `neuraltrade`) |
| Queue | Celery + Redis |
| Infra | Docker Compose, Nginx, Let's Encrypt SSL |
| CI/CD | GitHub Actions → AWS EC2 us-west-1 (54.183.178.141) |
| Data | Binance.US API (`api.binance.us` — NOT api.binance.com) |

---

## Supported Assets & Timeframes
- **Assets**: BTCUSD, ETHUSD, XAUUSD (PAXGUSDT on Binance), LTCUSD
- **Timeframes**: 5m, 15m, 30m, 1h, 2h, 4h, 1d

---

## Project Structure (key files)
```
intelligence-Automation-And-profit-Focused/
│
├── backfill_signals.py              ← Manual DB backfill script (run on AWS after deploy)
│
├── components/
│   └── ChartComponent.tsx           ← Main chart with signals, SL/Target lines, WebSocket
│
├── trading/
│   ├── views.py                     ← REST APIs: reversal-zones, signal-history
│   └── consumers.py                 ← WebSocket consumer: live price + signal broadcast
│
├── reversal_zones/
│   ├── reversal_calculator.py       ← THE CALCULATION ENGINE (Pine Script replica)
│   ├── tasks.py                     ← Celery tasks: save signals to DB, email alerts
│   ├── models.py                    ← ReversalZone DB model
│   ├── serializers.py               ← DRF serializers
│   └── views.py                     ← Reversal zone API views
│
├── signal_alerts/
│   └── email_utils.py               ← Email notification logic
│
└── app/
    ├── dashboard/page.tsx           ← Dashboard with live chart
    ├── history/page.tsx             ← Signal history page
    └── asset/[symbol]/page.tsx      ← Full-screen asset chart
```

---

## Signal Calculation — SINGLE SOURCE OF TRUTH

All signal values (Entry, SL, Target) flow through ONE engine:

```
reversal_calculator.py
    ↓  zones[i] = { center_price, stop_loss, target, is_bullish, timestamp, ... }
    ↓
[consumers.py WebSocket] OR [reversal_zones/tasks.py Celery] OR [backfill_signals.py]
    ↓
PostgreSQL DB → ReversalZone table
    ↓
trading/views.py API → frontend (live chart + history page)
```

### Pine Script Reversal Logic (reversal_calculator.py)
Exactly replicates TradingView Pine Script indicator "Reversal Entry Zones":
- **Preset**: Low (presetATR=2.8, presetPct=0.015)
- **ATR**: Wilder RMA (`alpha = 1/length`) — matches Pine `ta.atr()` exactly
- **Swing detection**: Running high/low with threshold = max(close×0.015/100, customAbs=0.05, 2.8×ATR)
- **confirm_bars**: 0 (matches Pine Script default input)
- **Open candle**: ALWAYS excluded (`n = len(df) - 1`) — prevents phantom signals
- **Alternation**: `strictly_alternating` final pass guarantees BUY→SELL→BUY output

### SL and Target Formula (ATR-based, professional)
```python
atr_distance = max(atr_at_signal_bar, price × 0.003)  # floor: 0.3% of price

# BUY signal:
stop_loss = entry - (1.0 × atr_distance)   # 1.0×ATR below entry
target    = entry + (2.0 × atr_distance)   # 2.0×ATR above entry (1:2 RR)

# SELL signal:
stop_loss = entry + (1.0 × atr_distance)   # 1.0×ATR above entry
target    = entry - (2.0 × atr_distance)   # 2.0×ATR below entry (1:2 RR)
```

### DB Save Rules (ALL writers must follow)
- `bar_index` → EXCLUDED from `update_or_create` defaults; set ONCE on INSERT only
- `stop_loss` + `target` → ALWAYS saved from calculator output
- Strict alternation enforced with `select_for_update()` transaction lock
- `_filter_new_only()` in Celery tasks prevents re-processing old signals
- Open candle dropped BEFORE calling `calculator.process_ohlcv_data(df)` in every caller

---

## Critical Bugs Fixed (DO NOT REVERT)

### 1. Signal Position Repainting (FIXED)
- **Root cause**: `bar_index` was in `update_or_create` defaults → shifted on every Celery run
- **Fix**: `bar_index` excluded from defaults; DB is the only display source in `get_reversal_zones`

### 2. Consecutive BUY/BUY or SELL/SELL (FIXED)
- **Root causes**: 4 independent layers now enforce alternation:
  1. `_emit_reversal()` in calculator blocks same-type at source
  2. `strictly_alternating` final pass in calculator output
  3. `select_for_update()` transaction in DB write functions
  4. `type_alternates` check on `live_pending` in `views.py`
  5. `lastSignalShape` + `typeAlternates` in `ChartComponent.tsx`

### 3. Phantom Signals vs TradingView (FIXED)
- **Root cause**: Binance API returns current open candle as last row; its high/low are incomplete
- **Fix**: `n = len(df) - 1` in calculator loop + `df = df.iloc[:-1]` in every caller

### 4. ATR Mismatch with TradingView (FIXED)
- **Root cause**: Python used EMA (`span=length`) but Pine uses Wilder RMA (`alpha=1/length`)
- **Fix**: `tr.ewm(alpha=1.0/length, adjust=False)` in `_atr()` function

### 5. History ≠ Live Chart Values (FIXED)
- **Root cause**: `backfill_signals.py` was NOT saving `stop_loss`/`target` to DB
- **Fix**: Added `"stop_loss": z.get("stop_loss")` and `"target": z.get("target")` to `save_zones()`

---

## Chart Signal Display (ChartComponent.tsx)

### Signal Markers
- BUY: green arrowUp below candle, labelled `BUY SIGNAL`
- SELL: red arrowDown above candle, labelled `SELL SIGNAL`
- Stored in `markersRef` (Map keyed by candle time, deduped)
- Persisted in `persistentSignalsRef` across timeframe changes

### SL / Entry / Target Lines
- Rendered via `chart.addLineSeries()` — SHORT horizontal segments (NOT full-width `createPriceLine`)
- Each signal gets 3 line series: Entry (white), SL (red), Target (green)
- Lines span: 1 candle before signal → 8 candles after signal
- Labels via `lastValueVisible: true` + `title` option (inline at line endpoint)
- Stored in `activePriceLines` ref; removed via `chartRef.current.removeSeries(ls)` on cleanup

### Signal Data Flow in Frontend
1. `fetchSignals()` calls:
   - `signal-history` API → DB signals (permanent, Step 1 — DB only)
   - `reversal-zones` API → filters `source === 'live_pending'` only (Step 2)
2. Merge: DB signals first, live_pending only if timestamp NEW + type ALTERNATES (Step 3)
3. `slTargetMapRef` stores `{sl, target, entry, isBullish}` per signal candle time
4. `renderSLTargetLines()` draws 3 line series per signal, called from `flushMarkers()`

### WebSocket (applySignal)
- Applies ONLY `newestZone` (last element of `all_zones[]`) — never full window redraw
- `typeAlternates` check prevents consecutive same-type from WebSocket

---

## API Endpoints

### Signal APIs
```
GET /api/trading/reversal-zones/<symbol>/?timeframe=15m
    Returns: DB signals + at most 1 live_pending zone
    live_pending: display timestamp = confirmation candle (current), NOT pivot bar

GET /api/trading/signal-history/<symbol>/?timeframe=15m
    Returns: DB records with center_price, stop_loss, target explicitly included
    Used by: history page + fetchSignals Step 1
```

### Signal History Response Shape
```json
{
  "success": true,
  "signals": [{
    "bar_index": 100,
    "center_price": 70253.92,
    "stop_loss": 69897.62,
    "target": 71027.57,
    "outer_top": 71027.57,
    "outer_bottom": 69897.62,
    "is_bullish": true,
    "label": "BUY",
    "timestamp": "2026-06-02T08:30:00+00:00",
    "source": "db"
  }]
}
```

### WebSocket URL
```
wss://smartriskfx.com/ws/market/<symbol>/<timeframe>/
```

---

## Database (PostgreSQL)

### ReversalZone Model (key fields)
```python
symbol          CharField(20)           # 'BTCUSDT'
timeframe       CharField(10)           # '15m'
reversal_time   DateTimeField           # pivot bar timestamp (NEVER changes after save)
center_price    DecimalField(20,8)      # entry price
stop_loss       DecimalField(20,8)      # ATR-based SL (nullable — old records may be NULL)
target          DecimalField(20,8)      # ATR-based Target (nullable — old records may be NULL)
outer_top       DecimalField(20,8)      # used as fallback if stop_loss/target NULL
outer_bottom    DecimalField(20,8)
is_bullish      BooleanField
label_text      CharField(10)           # 'BUY' or 'SELL'
bar_index       IntegerField            # SET ONCE ON INSERT — never updated
status          CharField(20)           # 'OPEN', 'TARGET_HIT', 'SL_HIT'

unique_together: ['symbol', 'timeframe', 'reversal_time']
```

---

## Deployment

### Server
- **IP**: 54.183.178.141 (AWS EC2 us-west-1)
- **SSH**: `ssh -i smartriskfx1.pem ubuntu@54.183.178.141`
- **Dir**: `~/smartrisk`
- **Container**: `django` (NOT "backend")
- **Env file**: `.env` (NOT .env.production)
- **Compose file**: `docker-compose.yml` (NOT docker-compose.prod.yml)

### CI/CD
Push to `main` → GitHub Actions → SSH → `git pull` → `docker-compose up -d --build` → migrate

### After Deploying DB Schema Changes
```bash
sudo docker-compose exec django python manage.py migrate
```

### After Deploying SL/Target Logic Changes (run once)
```bash
sudo docker-compose exec django python backfill_signals.py
# Recalculates and saves SL/Target for all historical signals
# Required when SL/Target formula changes (ensures history page matches live chart)
```

### Common Commands
```bash
sudo docker-compose ps                                    # status
sudo docker-compose logs -f django                        # backend logs
sudo docker-compose exec django python manage.py migrate  # run migrations
sudo docker-compose exec django python manage.py shell    # Django shell
sudo docker-compose restart django                        # restart backend
```

---

## Important Rules (Never Break These)

1. **Binance**: Always use `api.binance.us` (NOT api.binance.com — geo-restricted)
2. **Token name**: `access_token` in localStorage (NOT `auth_token`)
3. **Open candle**: ALWAYS drop `df.iloc[-1]` before calling `calculator.process_ohlcv_data(df)`
4. **bar_index**: NEVER in `update_or_create` defaults — set once on INSERT with `update_fields=["bar_index"]`
5. **SL/Target source**: ALWAYS from calculator output (`z.get("stop_loss")`, `z.get("target")`) — never recalculate elsewhere
6. **confirm_bars**: ALWAYS 0 in ALL calculator callers — matches Pine Script default
7. **ATR**: ALWAYS Wilder RMA (`ewm(alpha=1.0/length)`) — never EMA span=
8. **Alternation**: BUY→SELL→BUY strictly enforced at 4+ independent layers
9. **DB is source of truth**: `get_reversal_zones` serves DB records for display — never live calculator zones
10. **Backfill after formula changes**: Run `backfill_signals.py` on server after any SL/Target logic update
11. **Internal HTTP**: `NEXT_PUBLIC_API_URL=http://django:8000` inside Docker (nginx handles SSL externally)

---

## Files Changed in Latest Sessions (most recent first)
| File | What changed |
|---|---|
| `backfill_signals.py` | Added `stop_loss`/`target` to `save_zones()` defaults |
| `components/ChartComponent.tsx` | Per-signal short SL/Entry/Target line series; label at endpoint; alternation enforced |
| `trading/views.py` | `signal_history` now sends explicit `stop_loss`/`target`/`center_price`; `live_pending` uses ATR SL |
| `reversal_zones/reversal_calculator.py` | ATR→Wilder RMA; open candle skip; ATR-based SL/Target (1.0×/2.0×); final alternation pass; confirm_ts for live_pending display |
| `trading/consumers.py` | `bar_index` excluded from defaults; `confirm_bars=0`; open candle drop |
| `reversal_zones/tasks.py` | `bar_index` excluded; `_filter_new_only` in both tasks; `confirm_bars=0`; open candle drop |