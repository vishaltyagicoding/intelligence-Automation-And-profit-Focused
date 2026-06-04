# Signal Pipeline — Complete Reference

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    reversal_calculator.py                        │
│              (THE SINGLE CALCULATION ENGINE)                     │
│  • Pine Script exact replica (Wilder RMA ATR, confirm_bars=0)   │
│  • Outputs: center_price, stop_loss, target, timestamp          │
│  • SL = 1.0×ATR | Target = 2.0×ATR | 1:2 RR                    │
│  • Open candle ALWAYS excluded (n = len(df) - 1)                │
│  • Final alternation pass guarantees BUY→SELL→BUY output        │
└──────────────────┬──────────────────────────────────────────────┘
                   │
       ┌───────────┼────────────┬──────────────────┐
       │           │            │                  │
┌──────▼──────┐ ┌──▼──────┐ ┌──▼────────────┐ ┌──▼──────────────┐
│ consumers.py│ │tasks.py │ │backfill_      │ │  views.py        │
│ (WebSocket) │ │(Celery) │ │signals.py     │ │  live_pending    │
│ live candle │ │every 60s│ │(manual once)  │ │  detection only  │
└──────┬──────┘ └──┬──────┘ └──┬────────────┘ └──┬──────────────┘
       │           │            │                  │
       └───────────┴────────────┘                  │
                   │                               │
    ┌──────────────▼────────────────┐              │
    │    PostgreSQL DB               │              │
    │    (ReversalZone table)        │◄─────────────┘
    │    SINGLE SOURCE OF TRUTH      │   (DB records served,
    │    reversal_time NEVER changes │    live_pending for
    │    stop_loss/target ALWAYS set │    newest unsaved only)
    └──────────────┬────────────────┘
                   │
       ┌───────────┼──────────────────┐
       │           │                  │
┌──────▼──────┐ ┌──▼──────────┐ ┌────▼──────────────┐
│  views.py   │ │  views.py   │ │  email_utils.py    │
│ /reversal-  │ │ /signal-    │ │  (notifications)   │
│  zones/     │ │  history/   │ │  same SL/Target    │
└──────┬──────┘ └──┬──────────┘ └────────────────────┘
       │            │
       └────────────┘
                │
    ┌───────────▼───────────────────┐
    │      ChartComponent.tsx        │
    │  (frontend — single consumer) │
    │  STEP 1: DB signals (history) │
    │  STEP 2: live_pending filter  │
    │  STEP 3: merge + alternation  │
    │  SL/Target: addLineSeries()   │
    └───────────────────────────────┘
```

## File-by-File Responsibilities

### `reversal_zones/reversal_calculator.py`
**Role**: The ONLY place where signals are calculated.
**Never**: Duplicate this logic anywhere else.
**Key settings**:
```python
confirm_bars  = 0            # Pine Script default — MUST stay 0
atr formula   = ewm(alpha=1.0/length)  # Wilder RMA — NOT span=length (EMA)
n             = len(df) - 1  # Excludes open/live candle
strictly_alternating pass    # Final guarantee before returning zones[]
```
**Output per zone**:
```python
{
    'bar_index':     r.bar_index,       # pivot bar (for DB key)
    'center_price':  entry,             # entry price
    'stop_loss':     stop_loss,         # 1.0×ATR
    'target':        target,            # 2.0×ATR
    'is_bullish':    r.is_bullish,
    'label_text':    'BUY' or 'SELL',
    'reversal_time': ts,                # pivot timestamp (DB key)
    'timestamp':     ts,                # same
    'confirm_ts':    confirm_ts,        # newest zone only: confirmation candle ts
    'confirm_high':  confirm_high,      # for live_pending SL calculation
    'confirm_low':   confirm_low,       # for live_pending SL calculation
    'is_newest':     bool,              # True for last zone only
}
```

---

### `reversal_zones/tasks.py`
**Role**: Celery tasks — save confirmed signals to DB.
**Two tasks**:
1. `calculate_history_for_symbol_timeframe` (daily) — full history recalc
2. `calculate_reversal_zones` (incremental, 60s) — live new signals

**Rules enforced**:
- `df = df.iloc[:-1]` before calculator (open candle excluded)
- `_filter_new_only(zones, last_db)` — only process signals newer than last DB record
- `_save_zones_to_db()` — `bar_index` excluded from defaults; `stop_loss`/`target` ALWAYS saved
- `select_for_update()` in alternation check — prevents race condition duplicates

---

### `trading/consumers.py`
**Role**: WebSocket consumer — live price feed + save new signals on closed candles.

**Signal save** (`_save_signal_to_db`):
- `df = df.iloc[:-1]` before calculator
- `bar_index` excluded from `update_or_create` defaults
- `stop_loss` and `target` always saved from zone output

---

### `backfill_signals.py` (root)
**Role**: Manual one-time script — populates DB with historical signals.
**When to run**: After ANY formula change (SL/Target, ATR, etc.) to sync history page with live chart.
```bash
sudo docker-compose exec django python backfill_signals.py
```
**Rules**: Same as tasks.py — `bar_index` insert-only, `stop_loss`/`target` always saved.

---

### `trading/views.py`
**Role**: REST APIs served to frontend.

**`get_reversal_zones`** (`/api/trading/reversal-zones/<symbol>/`):
- Serves DB records as historical signals (no live calculator zones for display)
- Detects `live_pending` (newest calculator zone not yet in DB)
- `live_pending` display timestamp = confirmation candle (NOT pivot bar)
  → makes newest signal appear on current candle, not 6-8 bars back
- `type_alternates` check: live_pending rejected if same type as last DB signal

**`get_signal_history`** (`/api/trading/signal-history/<symbol>/`):
- Reads from DB only
- Explicitly sends `center_price`, `stop_loss`, `target` fields (needed by frontend)
- Used by: history page + `fetchSignals` Step 1 in ChartComponent

---

### `components/ChartComponent.tsx`
**Role**: Full trading chart with live candlesticks, signal markers, SL/Target lines.

**Signal fetch flow** (`fetchSignals`):
```
STEP 1: fetch /signal-history/ → DB signals (permanent, timestamped to pivot bar)
        → build dbLocalTimes set, build slTargetMapRef from stop_loss/target
STEP 2: fetch /reversal-zones/ → filter source==='live_pending' only
STEP 3: merge — DB signals first (persistent), pending only if new timestamp AND alternates
```

**SL/Target line rendering** (`renderSLTargetLines`):
- Called from `flushMarkers()` after every marker update
- `chart.addLineSeries()` for each signal's Entry/SL/Target
  - 1 candle before signal → 8 candles after signal (short, not full-width)
  - `lastValueVisible: true` + `title: "SL 70595.72"` → label at line endpoint
  - Entry: white (#e2e8f0), SL: red (#ef4444), Target: green (#10b981)
- Cleanup: `chartRef.current.removeSeries(ls)` (MUST use chart-level, not series-level)
- `slTargetMapRef` cleared on every `fetchSignals` call to prevent stale lines

**Critical refs**:
- `markersRef`: Map<time, marker> — one BUY/SELL arrow per candle
- `persistentSignalsRef`: Map<"asset:timeframe:time", marker> — survives timeframe switch
- `slTargetMapRef`: Map<time, {sl, target, entry, isBullish}> — for line rendering
- `activePriceLines`: line series array — cleaned up on timeframe/asset change

**WebSocket** (`applySignal`):
- Only `newestZone = s.all_zones[s.all_zones.length - 1]` applied
- `typeAlternates` check before adding to chart

---

## What "Confirmation Candle" Means

The reversal calculator detects a pivot on bar[i - confirm_bars] (= bar[i] when confirm_bars=0).
But this pivot bar may be 6-8 candles in the past (the highest/lowest swing point).

For DISPLAY purposes, `views.py` overrides the live_pending timestamp to the **confirmation candle**
(last closed bar = `df.index[-1]`), so the signal arrow appears on the current candle, not in the past.

For DB STORAGE, the original pivot timestamp is used (permanent record).

This means:
- **Live chart**: newest signal shows on current candle
- **History page**: that same signal shows on its actual pivot candle
- This is correct and intentional behaviour.

---

## Alternation Guarantee — 4 Independent Layers

| Layer | Where | Mechanism |
|---|---|---|
| 1 | `reversal_calculator.py` | `_emit_reversal()` skips same-type consecutive |
| 2 | `reversal_calculator.py` | `strictly_alternating` final pass on output |
| 3 | `reversal_zones/tasks.py` | `last_saved_label == new_label` check in `_save_zones_to_db` |
| 4 | `trading/views.py` | `type_alternates` check on `live_pending` zone |
| 5 | `ChartComponent.tsx` | `lastSignalShape` in fetchSignals + `typeAlternates` in applySignal |

---

## No-Repaint Guarantee — 6 Layers

| Layer | Where | Mechanism |
|---|---|---|
| 1 | `reversal_calculator.py` | Wilder RMA ATR (correct timing = correct bars) |
| 2 | `reversal_calculator.py` | `n = len(df) - 1` (open candle never processed) |
| 3 | All callers | `df = df.iloc[:-1]` before calculator call |
| 4 | All DB writers | `bar_index` excluded from defaults (set once on INSERT) |
| 5 | `trading/views.py` | DB records served for display (no live calculator zones) |
| 6 | `ChartComponent.tsx` | `persistentSignalsRef` + no full-window WebSocket redraw |