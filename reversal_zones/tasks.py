"""
Celery tasks for reversal signal history — production-ready.

TWO MODES
---------
1. calculate_all_history (daily at 00:30 UTC)
   Fetches full history window per timeframe, recalculates all signals,
   saves permanently to DB.

2. update_all_recent_signals (every 30 minutes)
   Fetches only recent candles, runs the Pine Script calculator,
   saves any NEW signals that appear after the last saved DB signal.
   This is the "continuously working Pine Script" the user requested.

LIVE SIGNALS (real-time, fires on every closed candle)
-------------------------------------------------------
_emit_live_signal() in consumers.py fires on every closed candle via
WebSocket and broadcasts immediately to all connected clients.
The 30-min task is the reliable fallback that ensures signals are
never missed even if WebSocket restarts or client is not connected.

SYMBOLS (all USDT format — consistent with Binance API and DB)
--------------------------------------------------------------
BTCUSDT, ETHUSDT, PAXGUSDT, LTCUSDT
"""

from celery import shared_task
import logging
import time
import requests as http_requests
import pandas as pd
from django.utils import timezone as tz
import pytz

logger = logging.getLogger(__name__)

# ── All symbols in BTCUSDT format (matches Binance API + DB) ─────────────────
SYMBOLS = ["BTCUSDT", "ETHUSDT", "PAXGUSDT", "LTCUSDT"]

ALL_TIMEFRAMES = ["5m", "15m", "30m", "1h", "2h", "4h", "1d"]

BINANCE_TF = {
    "5m": "5m",
    "15m": "15m", "30m": "30m", "1h": "1h",
    "2h": "2h", "4h": "4h", "1d": "1d",
}

# Full history window per timeframe (daily full recalculation)
DAYS_BACK = {
    "5m": 21,
    "15m": 30, "30m": 30, "1h": 30,
    "2h": 30,  "4h": 30,  "1d": 30,
}

# Recent window for 30-min incremental updates (hours)
RECENT_HOURS = {
    "5m": 24,
    "15m": 48, "30m": 72, "1h": 96,
    "2h": 120, "4h": 168, "1d": 720,
}


# ─────────────────────────────────────────────────────────────────────────────
def _fetch_binance_paginated(symbol: str, interval: str, days_back: int) -> pd.DataFrame:
    """Paginated Binance fetch for full history window."""
    end_ts   = int(time.time() * 1000)
    start_ts = int((time.time() - days_back * 86400) * 1000)
    return _fetch_range(symbol, interval, start_ts, end_ts)


def _fetch_binance_recent(symbol: str, interval: str, hours_back: int) -> pd.DataFrame:
    """Fetch only the most recent candles for incremental updates."""
    end_ts   = int(time.time() * 1000)
    start_ts = int((time.time() - hours_back * 3600) * 1000)
    return _fetch_range(symbol, interval, start_ts, end_ts)


def _fetch_range(symbol: str, interval: str, start_ts: int, end_ts: int) -> pd.DataFrame:
    """Core paginated Binance klines fetch."""
    all_rows = []
    current  = start_ts
    limit    = 1000

    while current < end_ts:
        url = (
            f"https://api.binance.us/api/v3/klines"
            f"?symbol={symbol}&interval={interval}"
            f"&startTime={current}&limit={limit}"
        )
        try:
            resp = http_requests.get(url, timeout=15)
            resp.raise_for_status()
            batch = resp.json()
        except Exception as e:
            logger.error("Binance fetch error [%s %s]: %s", symbol, interval, e)
            break

        if not batch:
            break

        all_rows.extend(batch)
        current = batch[-1][6] + 1  # next start = close_time + 1ms

        if len(batch) < limit:
            break

        time.sleep(0.25)

    if not all_rows:
        return pd.DataFrame()

    df = pd.DataFrame(all_rows, columns=[
        "timestamp", "open", "high", "low", "close", "volume",
        "close_time", "qv", "trades", "tbb", "tbq", "ignore"
    ])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
    for col in ["open", "high", "low", "close"]:
        df[col] = df[col].astype(float)
    df = df.set_index("timestamp")[["open", "high", "low", "close"]].sort_index()
    return df[~df.index.duplicated(keep="last")]


def _aggregate_10m(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate consecutive 5m candle pairs into 10m candles."""
    rows, times = [], []
    for i in range(0, len(df) - 1, 2):
        a, b = df.iloc[i], df.iloc[i + 1]
        rows.append({
            "open":  float(a["open"]),
            "high":  max(float(a["high"]), float(b["high"])),
            "low":   min(float(a["low"]),  float(b["low"])),
            "close": float(b["close"]),
        })
        times.append(df.index[i])
    return pd.DataFrame(rows, index=times)


def _get_last_db_signal(symbol: str, timeframe: str) -> dict | None:
    """Return {reversal_time, label_text} of the most recent DB signal, or None."""
    from reversal_zones.models import ReversalZone
    return (
        ReversalZone.objects
        .filter(symbol=symbol, timeframe=timeframe)
        .order_by("-reversal_time")
        .values("reversal_time", "label_text")
        .first()
    )


def _save_zones_to_db(symbol: str, timeframe: str, zones: list) -> int:
    """
    Bulk-save filtered zones to DB with STRICT alternation enforcement.
    Uses update_or_create on (symbol, timeframe, reversal_time).
    Returns count of newly created records.
    
    ALTERNATION ENFORCEMENT (MULTI-LAYER):
    1. Get the last saved signal from DB (before processing batch)
    2. Track the last label saved WITHIN this batch
    3. Before saving any signal, check BOTH DB and batch history
    4. If new signal has same label (BUY→BUY or SELL→SELL), SKIP IT
    5. This ensures PERFECT alternation: BUY → SELL → BUY → SELL
    
    NOTE: Email notifications are now sent automatically via Django signals
    (reversal_zones/signals.py) when new signals are created. This ensures
    INSTANT delivery at the exact moment the signal fires.
    """
    from reversal_zones.models import ReversalZone
    from django.db import IntegrityError

    saved = 0
    skipped_violations = 0
    
    # ── Get the LAST signal from DB (before processing this batch) ────────────
    last_db_signal = (
        ReversalZone.objects
        .filter(symbol=symbol, timeframe=timeframe)
        .order_by("-reversal_time")
        .values("label_text", "reversal_time")
        .first()
    )
    
    # Track the last label saved in THIS batch (for within-batch alternation check)
    last_saved_label = last_db_signal["label_text"] if last_db_signal else None
    
    # Sort zones by timestamp to process in chronological order
    zones_sorted = sorted(zones, key=lambda z: z.get("timestamp") or z.get("reversal_time"))
    
    for z in zones_sorted:
        try:
            ts = z.get("timestamp") or z.get("reversal_time")
            if isinstance(ts, str):
                from django.utils.dateparse import parse_datetime
                reversal_time = parse_datetime(ts)
            elif hasattr(ts, "to_pydatetime"):
                reversal_time = ts.to_pydatetime()
            else:
                reversal_time = ts

            if reversal_time is None:
                continue
            if reversal_time.tzinfo is None:
                reversal_time = pytz.utc.localize(reversal_time)

            is_bull = z.get("is_bullish", True)
            new_label = "BUY" if is_bull else "SELL"

            # ── ALTERNATION CHECK: Compare with last saved label ──────────────
            # Check against BOTH: last DB signal AND last signal saved in this batch
            if last_saved_label == new_label:
                logger.warning(
                    "🛡️ ALTERNATION VIOLATION BLOCKED: %s→%s at %s [%s %s]",
                    last_saved_label,
                    new_label,
                    reversal_time.strftime("%Y-%m-%d %H:%M:%S"),
                    symbol,
                    timeframe
                )
                skipped_violations += 1
                continue  # SKIP this signal

            # ── Save signal (alternation is valid) ────────────────────────────
            zone, created = ReversalZone.objects.update_or_create(
                symbol        = symbol,
                timeframe     = timeframe,
                reversal_time = reversal_time,
                defaults={
                    "center_price": z["center_price"],
                    "outer_top":    z["outer_top"],
                    "outer_bottom": z["outer_bottom"],
                    "core_top":     z["core_top"],
                    "core_bottom":  z["core_bottom"],
                    "is_bullish":   is_bull,
                    "label_text":   new_label,
                    "bar_index":    z.get("bar_index", 0),
                },
            )
            if created:
                saved += 1
                # Update last_saved_label for next iteration (within-batch tracking)
                last_saved_label = new_label
                logger.info(
                    "✅ Signal saved: %s at %s [%s %s]",
                    new_label,
                    reversal_time.strftime("%Y-%m-%d %H:%M:%S"),
                    symbol,
                    timeframe
                )
                # Email is sent automatically by Django signal (reversal_zones/signals.py)

        except (IntegrityError, Exception) as e:
            msg = str(e)
            if "Consecutive" in msg and "signals not allowed" in msg:
                logger.info("🛡️ DB constraint blocked consecutive signal [%s %s]", symbol, timeframe)
                skipped_violations += 1
            else:
                logger.error("Error saving zone [%s %s]: %s", symbol, timeframe, e)

    if skipped_violations > 0:
        logger.info(
            "🛡️ Alternation enforcement: skipped %d violations [%s %s]",
            skipped_violations,
            symbol,
            timeframe
        )

    return saved


def _filter_new_only(zones: list, last_db: dict | None) -> list:
    """Return only zones that occur AFTER the last DB signal timestamp."""
    if not last_db or not zones:
        return zones

    last_time = last_db["reversal_time"]
    if last_time.tzinfo is None:
        last_time = pytz.utc.localize(last_time)

    new = []
    for z in zones:
        ts = z.get("timestamp") or z.get("reversal_time")
        if isinstance(ts, str):
            from django.utils.dateparse import parse_datetime
            zt = parse_datetime(ts)
        elif hasattr(ts, "to_pydatetime"):
            zt = ts.to_pydatetime()
        else:
            zt = ts

        if zt is None:
            continue
        if zt.tzinfo is None:
            zt = pytz.utc.localize(zt)

        if zt > last_time:
            new.append(z)

    return new


# Binance internal symbol → user-facing symbol (matches SignalAlert.crypto in DB)
_BINANCE_TO_USER_SYMBOL = {
    'BTCUSDT':  'BTCUSD',
    'ETHUSDT':  'ETHUSD',
    'LTCUSDT':  'LTCUSD',
    'PAXGUSDT': 'XAUUSD',   # Gold: stored as XAUUSD in user alerts
    'XAUUSDT':  'XAUUSD',
}


# ─────────────────────────────────────────────────────────────────────────────
# TASK 1: Full daily recalculation
# ─────────────────────────────────────────────────────────────────────────────
@shared_task(bind=True, max_retries=2, default_retry_delay=60)
def calculate_history_for_symbol_timeframe(self, symbol: str, timeframe: str):
    """
    Full history recalculation for one symbol+timeframe.
    Called by calculate_all_history() daily.
    """
    from reversal_zones.signal_filter import AntiChopFilter

    binance_tf = BINANCE_TF.get(timeframe, "1h")
    days_back  = DAYS_BACK.get(timeframe, 30)

    logger.info("📊 Full history: %s %s (%d days)", symbol, timeframe, days_back)

    try:
        df = _fetch_binance_paginated(symbol, binance_tf, days_back)

        if df.empty or len(df) < 20:
            logger.warning("Not enough data: %s %s", symbol, timeframe)
            return {"status": "no_data"}

        result = AntiChopFilter(timeframe=timeframe).process(df)
        zones  = result.get("zones", [])
        saved  = _save_zones_to_db(symbol, timeframe, zones)

        logger.info("✅ Full history done: %s %s — %d zones, %d new saved",
                    symbol, timeframe, len(zones), saved)
        return {"status": "ok", "signals": len(zones), "saved_new": saved}

    except Exception as exc:
        logger.error("❌ Full history error [%s %s]: %s", symbol, timeframe, exc)
        try:
            self.retry(exc=exc)
        except Exception:
            return {"status": "error", "error": str(exc)}


# ─────────────────────────────────────────────────────────────────────────────
# TASK 2: 30-minute incremental update (the "continuously working" task)
# ─────────────────────────────────────────────────────────────────────────────
@shared_task(bind=True, max_retries=1, default_retry_delay=30)
def update_recent_signals_for_symbol_timeframe(self, symbol: str, timeframe: str):
    """
    Incremental update: fetch recent candles, run Pine Script logic,
    save any NEW signals that appear after the last saved DB signal.

    This is the task that makes signal detection CONTINUOUS.
    Runs every 30 minutes for all 4 symbols × 7 timeframes = 28 tasks.
    """
    from reversal_zones.signal_filter import AntiChopFilter

    binance_tf = BINANCE_TF.get(timeframe, "1h")
    hours_back = RECENT_HOURS.get(timeframe, 48)

    try:
        last_db = _get_last_db_signal(symbol, timeframe)

        df = _fetch_binance_recent(symbol, binance_tf, hours_back)
        if df.empty or len(df) < 20:
            return {"status": "no_data"}

        result    = AntiChopFilter(timeframe=timeframe).process(df)
        all_zones = result.get("zones", [])

        # Only save zones that are NEW (after last DB signal)
        new_zones = _filter_new_only(all_zones, last_db)

        if not new_zones:
            logger.debug("No new signals: %s %s", symbol, timeframe)
            return {"status": "no_new_signals"}

        saved = _save_zones_to_db(symbol, timeframe, new_zones)

        if saved > 0:
            logger.info("📈 %d NEW signal(s) saved: %s %s", saved, symbol, timeframe)

        return {
            "status":    "ok",
            "symbol":    symbol,
            "timeframe": timeframe,
            "new_zones": len(new_zones),
            "saved":     saved,
        }

    except Exception as exc:
        logger.error("Error in incremental update [%s %s]: %s", symbol, timeframe, exc)
        try:
            self.retry(exc=exc)
        except Exception:
            return {"status": "error", "error": str(exc)}


# ─────────────────────────────────────────────────────────────────────────────
# Fan-out tasks
# ─────────────────────────────────────────────────────────────────────────────
@shared_task
def calculate_all_history():
    """Full 30-day recalculation for all symbols × timeframes. Runs daily."""
    logger.info("🚀 Daily full history recalculation starting...")
    count = 0
    for symbol in SYMBOLS:
        for tf in ALL_TIMEFRAMES:
            calculate_history_for_symbol_timeframe.apply_async(
                args=[symbol, tf],
                countdown=count * 2,
            )
            count += 1
    logger.info("📋 Queued %d full-history tasks", count)
    return {"queued": count}


@shared_task
def update_all_recent_signals():
    """
    Incremental signal update for all symbols × timeframes.
    Runs every 5 minutes — this is the reliable FALLBACK that catches signals
    missed while WebSocket was down (primary path: _emit_live_signal in consumers.py).
    """
    logger.info("🔄 5-min incremental signal update starting...")
    count = 0
    for symbol in SYMBOLS:
        for tf in ALL_TIMEFRAMES:
            # No countdown delay — dispatch immediately for fastest execution
            update_recent_signals_for_symbol_timeframe.apply_async(
                args=[symbol, tf],
            )
            count += 1
    logger.info("📋 Queued %d incremental tasks", count)
    return {"queued": count}


# ── Backward-compatible aliases ───────────────────────────────────────────────
@shared_task
def calculate_all_symbols_task():
    return calculate_all_history.apply_async()


@shared_task
def initialize_reversal_zones():
    return calculate_all_history.apply_async()


@shared_task
def calculate_reversal_zones_task(symbol, timeframe):
    return calculate_history_for_symbol_timeframe.apply_async(args=[symbol, timeframe])