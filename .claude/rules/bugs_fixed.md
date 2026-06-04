# Bugs Fixed — Complete History

This file documents every significant bug fixed in the project.
Read this BEFORE making any changes to avoid reverting fixes.

---

## BUG-001: Signal Repainting / Position Shifting
**Symptom**: BUY/SELL arrows on chart would shift to different candles on page refresh or after new candles.
**Root causes (5 vectors)**:
1. `bar_index` was in `update_or_create` defaults → every Celery run shifted it
2. `get_reversal_zones` API returned LIVE calculator zones (not DB records) → different timestamps each call
3. WebSocket `applySignal` mapped ALL zones from window → full window redraw each signal
4. `backfill_signals.py` had `bar_index` in defaults → backfill shifted positions
5. Daily Celery task called `_save_zones_to_db` without `_filter_new_only` → re-processed old signals

**Fix locations**:
- `consumers.py`: `bar_index` excluded from defaults; set with `update_fields=["bar_index"]` on INSERT
- `reversal_zones/tasks.py`: same bar_index fix; added `_filter_new_only` to daily task
- `backfill_signals.py`: same bar_index fix
- `trading/views.py`: `get_reversal_zones` now reads DB records; live calculator used only for live_pending
- `ChartComponent.tsx`: `applySignal` uses only `newestZone`; `persistentSignalsRef` preserves positions

**NEVER revert**: bar_index must never appear in update_or_create defaults.

---

## BUG-002: Consecutive BUY/BUY or SELL/SELL Signals
**Symptom**: Chart showed BUY→BUY or SELL→SELL arrows on consecutive candles.
**Root causes**:
1. Calculator's `_emit_reversal` had no consecutive-type check
2. `live_pending` zone in views.py had no alternation check (only timestamp check)
3. WebSocket `applySignal` had no alternation check
4. `fetchSignals` live_pending had no alternation check

**Fix locations**:
- `reversal_calculator.py`: `_emit_reversal()` now checks `last_reversal.is_bullish == is_bullish`
- `reversal_calculator.py`: `strictly_alternating` final pass on output list
- `trading/views.py`: `type_alternates = (last_db_label is None) or (last_db_label != nl_label)`
- `ChartComponent.tsx`: `lastSignalShape` check in fetchSignals; `typeAlternates` in applySignal

**NEVER revert**: All 4+ alternation layers must stay intact.

---

## BUG-003: Phantom Signals (not matching TradingView)
**Symptom**: Website showed a BUY signal that TradingView did NOT show at the same time.
**Root cause**: Binance klines API returns the current OPEN (unfinished) candle as the last row.
Its high/low are changing every tick. Calculator processing it generates signals that Pine Script
(which only fires on CLOSED candles) would never confirm.

**Fix locations**:
- `reversal_calculator.py`: `n = len(df) - 1` in main loop — open candle never enters loop
- `trading/views.py`: `if len(df) > 1: df = df.iloc[:-1]` before calculator
- `reversal_zones/tasks.py`: same `df.iloc[:-1]` in both daily and incremental tasks
- `trading/consumers.py`: same `df.iloc[:-1]`
- `backfill_signals.py`: same `df.iloc[:-1]`

**NEVER revert**: Open candle must always be dropped. All 5 files have this protection.

---

## BUG-004: ATR Mismatch → Signals on Wrong Candles
**Symptom**: Signals appeared on slightly different candles than TradingView.
**Root cause**: Python used `ewm(span=length)` = EMA (alpha=2/(length+1)) but Pine uses Wilder RMA (alpha=1/length).
For length=5: EMA alpha=0.333 vs RMA alpha=0.200 — significant difference in ATR values → different thresholds → different signal timing.

**Fix location**: `reversal_zones/reversal_calculator.py` `_atr()` function:
```python
# WRONG (was):
return tr.ewm(span=length, adjust=False).mean()
# CORRECT (now):
return tr.ewm(alpha=1.0 / length, adjust=False).mean()   # Wilder RMA = Pine ta.atr()
```
Note: `_ema()` still correctly uses `ewm(span=length)` — that IS the correct EMA formula.

**NEVER revert**: The ATR function must use `alpha=1.0/length`.

---

## BUG-005: confirm_bars=1 (Wrong Timing)
**Symptom**: Signals appeared 1 candle earlier than TradingView.
**Root cause**: All calculator callers had `confirm_bars=1` but Pine Script default is `confirmBars = input.int(0, ...)` = 0.

**Fix**: All callers now use `confirm_bars=0`:
- `trading/views.py`
- `trading/consumers.py`
- `reversal_zones/tasks.py` (both tasks)
- `backfill_signals.py`

**NEVER revert**: confirm_bars must be 0 in ALL callers.

---

## BUG-006: History Page ≠ Live Chart (Different SL/Target Values)
**Symptom**: History page showed different or missing SL/Target values compared to live chart.
**Root causes**:
1. `backfill_signals.py` `save_zones()` was NOT saving `stop_loss` or `target` to DB
2. `signal-history` API was NOT sending `stop_loss`/`target`/`center_price` fields explicitly
3. Old SL/Target formula: used candle high/low directly → only 30-40 points (too tight)

**Fix locations**:
- `backfill_signals.py`: Added `"stop_loss": z.get("stop_loss")` and `"target": z.get("target")` to defaults
- `trading/views.py` `get_signal_history`: Added explicit `stop_loss`, `target`, `center_price` fields in response
- `reversal_calculator.py`: Changed to ATR-based formula (1.0×ATR / 2.0×ATR)
- **Action required on server**: `python backfill_signals.py` to populate NULL records

---

## BUG-007: SL/Target Lines Full-Width (Cluttered Chart)
**Symptom**: Red and green lines stretched across entire chart width; dozens of overlapping labels on right axis.
**Root cause**: `createPriceLine()` in lightweight-charts always draws full-width — cannot be shortened.
Also: ALL historical signals were stored in `slTargetMapRef` and all rendered simultaneously.

**Fix**: Replaced with `chart.addLineSeries()` per signal:
- Each line series has 2 data points: `signal_time - 1 candle` → `signal_time + 8 candles`
- Short, clean line segments per signal
- `lastValueVisible: true` + `title` option for inline label at endpoint
- Cleanup: `chartRef.current.removeSeries(ls)` (not `series.removePriceLine()`)

**NEVER revert**: Do not use `createPriceLine()` for SL/Target — it always spans full chart width.

---

## BUG-008: TypeScript Error — center_price Not in pendingRaw Type
**Symptom**: TypeScript build error: "Property 'center_price' does not exist on type..."
**Root cause**: `pendingRaw` array was typed without `center_price` field.
**Fix**: Added `center_price?: number` to pendingRaw type declaration in `ChartComponent.tsx`.

---

## BUG-009: SL/Target Labels Below/Above Line (Not Inline)
**Symptom**: SL/Target labels appeared below the line endpoint, not horizontally aligned.
**Root cause**: `setMarkers()` on line series with `position: 'inBar'` always offsets text above/below the anchor point — it cannot render truly inline.
**Fix**: Removed `setMarkers()` calls. Used `lastValueVisible: true` + `title` option which renders the label on the right price axis at the exact price level, horizontally aligned with the line.

---

## BUG-010: ivl Not Found in renderSLTargetLines
**Symptom**: TypeScript error: "Cannot find name 'ivl'"
**Root cause**: `ivl` is defined inside `fetchSignals` scope, but `renderSLTargetLines` is outside that scope.
**Fix**: Changed to `TF_SEC[timeframe]` inside `renderSLTargetLines` instead of `ivl`.