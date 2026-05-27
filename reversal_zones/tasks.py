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

# ── Redis client for task heartbeat + distributed lock ────────────────────────
def _get_task_redis():
    """Dedicated Redis client (DB=4) for task scheduling metadata."""
    import redis as _r
    from django.conf import settings
    return _r.Redis(
        host=getattr(settings, 'REDIS_HOST', 'redis'),
        port=getattr(settings, 'REDIS_PORT', 6379),
        db=4,
        socket_connect_timeout=2,
        socket_timeout=2,
        decode_responses=True,
    )

HEARTBEAT_KEY  = 'beat:heartbeat:update_all_recent_signals'
LOCK_KEY       = 'lock:update_all_recent_signals'
HEARTBEAT_TTL  = 300   # 5 min — if key expires, beat is dead

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

# Recent window for 60-second incremental updates (DAYS, not hours).
# CRITICAL: Must use the SAME window as daily task to ensure calculator
# produces IDENTICAL signals. Using a shorter window causes the calculator
# to see different swing patterns and emit signals at different positions.
#
# All timeframes now use 30 DAYS to match the daily full history task.
# This ensures perfect consistency across all signal generation paths.
RECENT_DAYS = {
    "5m":  30,   # 30 days = 8640 candles (plenty for EMA warmup)
    "15m": 30,   # 30 days = 2880 candles
    "30m": 30,   # 30 days = 1440 candles
    "1h":  30,   # 30 days = 720 candles
    "2h":  30,   # 30 days = 360 candles
    "4h":  30,   # 30 days = 180 candles
    "1d":  30,   # 30 days = 30 candles
}


# ─────────────────────────────────────────────────────────────────────────────
def _fetch_binance_paginated(symbol: str, interval: str, days_back: int) -> pd.DataFrame:
    """Paginated Binance fetch for full history window."""
    end_ts   = int(time.time() * 1000)
    start_ts = int((time.time() - days_back * 86400) * 1000)
    return _fetch_range(symbol, interval, start_ts, end_ts)


def _fetch_binance_recent(symbol: str, interval: str, days_back: int) -> pd.DataFrame:
    """Fetch recent candles for incremental updates (now uses DAYS to match full history)."""
    end_ts   = int(time.time() * 1000)
    start_ts = int((time.time() - days_back * 86400) * 1000)
    return _fetch_range(symbol, interval, start_ts, end_ts)


def _fetch_range(symbol: str, interval: str, start_ts: int, end_ts: int) -> pd.DataFrame:
    """
    Core paginated Binance klines fetch.
    
    CRITICAL: Uses Binance.com (global) - same data source as TradingView.
    This ensures signals match TradingView exactly.
    """
    all_rows = []
    current  = start_ts
    limit    = 1000

    while current < end_ts:
        url = (
            f"https://api.binance.com/api/v3/klines"
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
    Save new zones to DB with strict alternation enforcement and a
    DB-level advisory lock to prevent race conditions between the
    Celery task path and the WebSocket consumer path running simultaneously.

    Returns count of newly created records.
    Emails are sent automatically via Django post_save signal.
    """
    from reversal_zones.models import ReversalZone
    from django.db import IntegrityError, transaction

    saved = 0
    skipped_violations = 0

    # Sort zones chronologically — always process oldest → newest
    zones_sorted = sorted(
        zones,
        key=lambda z: z.get("timestamp") or z.get("reversal_time")
    )

    # Wrap in atomic transaction with select_for_update to serialize
    # concurrent saves from Celery task + WebSocket consumer
    with transaction.atomic():
        # Re-read last signal INSIDE the transaction with row lock
        last_row = (
            ReversalZone.objects
            .filter(symbol=symbol, timeframe=timeframe)
            .select_for_update()           # advisory lock — serializes saves
            .order_by("-reversal_time")
            .values("label_text", "reversal_time")
            .first()
        )
        last_saved_label = last_row["label_text"] if last_row else None

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

                is_bull   = z.get("is_bullish", True)
                new_label = "BUY" if is_bull else "SELL"

                # ── ALTERNATION CHECK ─────────────────────────────────────────
                if last_saved_label == new_label:
                    logger.warning(
                        "🛡️ ALTERNATION BLOCKED: %s→%s at %s [%s %s]",
                        last_saved_label, new_label,
                        reversal_time.strftime("%Y-%m-%d %H:%M:%S"),
                        symbol, timeframe,
                    )
                    skipped_violations += 1
                    continue

                # ── Save signal ───────────────────────────────────────────────
                zone_obj, created = ReversalZone.objects.update_or_create(
                    symbol        = symbol,
                    timeframe     = timeframe,
                    reversal_time = reversal_time,
                    defaults={
                        "center_price": z["center_price"],
                        "stop_loss":    z.get("stop_loss"),
                        "target":       z.get("target"),
                        "outer_top":    z["outer_top"],
                        "outer_bottom": z["outer_bottom"],
                        "core_top":     z["core_top"],
                        "core_bottom":  z["core_bottom"],
                        "is_bullish":   is_bull,
                        "label_text":   new_label,
                        # bar_index EXCLUDED from defaults intentionally.
                        # update_or_create applies defaults on both INSERT *and* UPDATE.
                        # bar_index is a relative offset in the current data window and
                        # shifts every time the window grows. Updating it on every Celery
                        # run would silently repaint historical signal positions.
                        # It is set once on INSERT (see below) and never touched again.
                    },
                )
                if created:
                    # Set bar_index once on first insert only — never update after
                    zone_obj.bar_index = z.get("bar_index", 0)
                    zone_obj.save(update_fields=["bar_index"])
                    saved += 1
                    last_saved_label = new_label
                    logger.info(
                        "✅ Saved NEW %s signal [%s %s] @ %.4f  time=%s",
                        new_label, symbol, timeframe,
                        float(z["center_price"]),
                        reversal_time.strftime("%Y-%m-%d %H:%M:%S UTC"),
                    )

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
    """
    Return only zones that are AFTER the last saved DB signal timestamp.

    IMPORTANT: We do NOT apply a time-based freshness cutoff here because
    `reversal_time` is the candle's CLOSE timestamp, not when it was detected.
    A 4H candle that closed at 08:00 and gets detected at 09:30 has
    reversal_time=08:00 — a 30-min cutoff would block it entirely.

    The only cutoff that matters is:
    - If DB has a previous signal: zone must be AFTER that signal's reversal_time
    - If DB is empty (fresh deploy): only save zones from last 2 hours maximum
      to prevent emailing days-old historical signals after a DB wipe.

    The 10-min freshness in signals.py (using created_at) handles preventing
    old DB rows from triggering emails.
    """
    from datetime import datetime, timedelta as _td
    now_utc = datetime.now(pytz.utc)

    # When DB is empty: only process signals from the last 2 hours
    # This prevents emailing 2-3 day old signals after a fresh DB wipe/deploy.
    # 2 hours is generous enough to catch any timeframe (even 1H/4H) correctly.
    empty_db_cutoff = now_utc - _td(hours=2)

    # Normalise last_db timestamp once
    last_time = None
    if last_db and last_db.get("reversal_time"):
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

        if last_time is not None:
            # DB has data: only accept zones after the last known signal
            if zt <= last_time:
                continue
        else:
            # DB is empty: only accept zones from last 2 hours (anti-spam guard)
            if zt < empty_db_cutoff:
                continue

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
    from reversal_zones.reversal_calculator import ReversalZoneCalculator

    binance_tf = BINANCE_TF.get(timeframe, "1h")
    days_back  = DAYS_BACK.get(timeframe, 30)

    logger.info("📊 Full history: %s %s (%d days)", symbol, timeframe, days_back)

    try:
        df = _fetch_binance_paginated(symbol, binance_tf, days_back)

        if df.empty or len(df) < 20:
            logger.warning("Not enough data: %s %s", symbol, timeframe)
            return {"status": "no_data"}

        # Use RAW calculator (matches TradingView Pine Script EXACTLY)
        # NO additional filters (ADX, RSI, time gaps) - just pure swing tracking
        # 
        # CRITICAL: confirmBars = 1 adds 1-candle confirmation delay to match TradingView
        # This prevents premature signals that haven't been confirmed yet
        calculator = ReversalZoneCalculator(
            preset="Low",
            calc_mode="Average",
            avg_len=5,
            atr_len=5,
            custom_abs=0.05,
            confirm_bars=1,  # ← CHANGED from 0 to 1 for confirmation
            timeframe=timeframe
        )
        result = calculator.process_ohlcv_data(df)
        zones  = result.get("zones", [])

        # ANTI-REPAINT FIX: daily task must also use _filter_new_only.
        # Without this filter, the task would call update_or_create on signals
        # that already exist in DB. Even though bar_index is now excluded from
        # defaults, the task would still perform unnecessary DB writes and could
        # theoretically overwrite center_price/outer_top/bottom if the calculator
        # produces slightly different values on a new window run.
        # Using _filter_new_only(zones, last_db) ensures we ONLY insert truly new
        # signals — records already in DB are completely untouched.
        last_db = _get_last_db_signal(symbol, timeframe)
        new_zones = _filter_new_only(zones, last_db)
        saved  = _save_zones_to_db(symbol, timeframe, new_zones)

        logger.info("✅ Full history done: %s %s — %d zones found, %d new saved",
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
    from reversal_zones.reversal_calculator import ReversalZoneCalculator

    binance_tf = BINANCE_TF.get(timeframe, "1h")
    days_back  = RECENT_DAYS.get(timeframe, 30)

    try:
        last_db = _get_last_db_signal(symbol, timeframe)

        df = _fetch_binance_recent(symbol, binance_tf, days_back)
        if df.empty or len(df) < 20:
            return {"status": "no_data"}

        # Use RAW calculator (matches TradingView Pine Script EXACTLY)
        # NO additional filters (ADX, RSI, time gaps) - just pure swing tracking
        #
        # CRITICAL: confirmBars = 1 adds 1-candle confirmation delay to match TradingView
        # This prevents premature signals that haven't been confirmed yet
        calculator = ReversalZoneCalculator(
            preset="Low",
            calc_mode="Average",
            avg_len=5,
            atr_len=5,
            custom_abs=0.05,
            confirm_bars=1,  # ← CHANGED from 0 to 1 for confirmation
            timeframe=timeframe
        )
        result    = calculator.process_ohlcv_data(df)
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


@shared_task(bind=True, max_retries=0)
def update_all_recent_signals(self):
    """
    SELF-PERPETUATING signal update — never depends solely on celery-beat.

    THREE-LAYER reliability:
      Layer 1 — celery-beat triggers this every 60 seconds (settings.py)
      Layer 2 — task reschedules ITSELF at the end (self-perpetuating chain)
                 so it keeps running even if celery-beat crashes or is misconfigured
      Layer 3 — Redis distributed lock prevents overlap if both layers fire at once

    If celery-beat is broken: task still runs every 60 sec via self-scheduling.
    If celery-worker is broken: celery-beat re-queues on worker recovery.
    Both broken simultaneously: monitoring alert fires (see HEARTBEAT_KEY in Redis).
    """
    r = None
    lock_acquired = False
    try:
        r = _get_task_redis()
        # ── Distributed lock — prevent two instances running simultaneously ──
        lock_acquired = r.set(LOCK_KEY, "1", nx=True, ex=90)
        if not lock_acquired:
            logger.debug("update_all_recent_signals: skipping (another instance running)")
            return {"status": "skipped_locked"}

        # ── Heartbeat: update timestamp so monitoring knows beat is alive ────
        r.set(HEARTBEAT_KEY, str(int(time.time())), ex=HEARTBEAT_TTL)

    except Exception as redis_err:
        logger.warning("Redis unavailable in update_all_recent_signals: %s", redis_err)
        # Continue anyway — signal detection is more important than Redis

    logger.info("🔄 Signal update starting (self-perpetuating)...")
    count = 0
    try:
        for symbol in SYMBOLS:
            for tf in ALL_TIMEFRAMES:
                update_recent_signals_for_symbol_timeframe.apply_async(
                    args=[symbol, tf],
                )
                count += 1
        logger.info("📋 Queued %d signal-check tasks", count)
    finally:
        # ── Release lock ─────────────────────────────────────────────────────
        if lock_acquired and r:
            try:
                r.delete(LOCK_KEY)
            except Exception:
                pass

        # ── LAYER 2: Self-reschedule in 60 seconds ────────────────────────────
        # This runs regardless of celery-beat status.
        # Even if someone accidentally changes back to DatabaseScheduler or
        # deletes the PeriodicTask, signals will keep running every 60 seconds.
        try:
            update_all_recent_signals.apply_async(countdown=60)
            logger.debug("♻️ Self-rescheduled in 60 seconds")
        except Exception as sched_err:
            logger.error("Self-reschedule failed (beat is now the only trigger): %s", sched_err)

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



# ─────────────────────────────────────────────────────────────────────────────
# TASK 3: Check and update signal statuses (Target Hit / SL Hit)
# ─────────────────────────────────────────────────────────────────────────────
@shared_task(max_retries=1, default_retry_delay=30)
def check_signal_statuses():
    """
    Check all OPEN signals and update their status to TARGET_HIT or SL_HIT
    based on price movements since signal generation.
    
    Runs every 5 minutes to keep history page status up-to-date.
    
    Logic:
    - For BUY signals: Check if price reached target (above) before stop loss (below)
    - For SELL signals: Check if price reached target (below) before stop loss (above)
    - Once status changes from OPEN, it never changes again (permanent record)
    """
    from reversal_zones.models import ReversalZone
    from django.utils import timezone as tz
    from datetime import timedelta
    
    logger.info("🔍 Checking signal statuses...")
    
    updated_count = 0
    checked_count = 0
    
    try:
        # Get all OPEN signals from last 30 days
        since = tz.now() - timedelta(days=30)
        open_signals = ReversalZone.objects.filter(
            status='OPEN',
            reversal_time__gte=since
        ).select_related()
        
        # Group by symbol for efficient API calls
        signals_by_symbol = {}
        for signal in open_signals:
            if signal.symbol not in signals_by_symbol:
                signals_by_symbol[signal.symbol] = []
            signals_by_symbol[signal.symbol].append(signal)
        
        # Check each symbol's signals
        for symbol, signals in signals_by_symbol.items():
            try:
                # Fetch recent price data for this symbol
                # Use 1m timeframe for precise target/SL hit detection
                df = _fetch_binance_recent(symbol, "1m", days_back=30)
                
                if df.empty:
                    logger.warning(f"No price data for {symbol}, skipping")
                    continue
                
                # Check each signal
                for signal in signals:
                    checked_count += 1
                    
                    # Get price data after signal time
                    signal_time = signal.reversal_time
                    if signal_time.tzinfo is None:
                        signal_time = pytz.utc.localize(signal_time)
                    
                    # Filter candles after signal
                    future_candles = df[df.index > signal_time]
                    
                    if future_candles.empty:
                        continue
                    
                    # Check if target or stop loss was hit
                    target_hit = False
                    sl_hit = False
                    hit_time = None
                    
                    if signal.is_bullish:
                        # BUY signal: target above, stop loss below
                        for idx, candle in future_candles.iterrows():
                            # Check if stop loss hit first (price went below SL)
                            if float(candle['low']) <= float(signal.stop_loss):
                                sl_hit = True
                                hit_time = idx
                                break
                            # Check if target hit (price went above target)
                            if float(candle['high']) >= float(signal.target):
                                target_hit = True
                                hit_time = idx
                                break
                    else:
                        # SELL signal: target below, stop loss above
                        for idx, candle in future_candles.iterrows():
                            # Check if stop loss hit first (price went above SL)
                            if float(candle['high']) >= float(signal.stop_loss):
                                sl_hit = True
                                hit_time = idx
                                break
                            # Check if target hit (price went below target)
                            if float(candle['low']) <= float(signal.target):
                                target_hit = True
                                hit_time = idx
                                break
                    
                    # Update status if target or SL was hit
                    if target_hit:
                        signal.status = 'TARGET_HIT'
                        signal.status_updated_at = hit_time
                        signal.save(update_fields=['status', 'status_updated_at'])
                        updated_count += 1
                        logger.info(f"✅ Target Hit: {symbol} {signal.timeframe} {'BUY' if signal.is_bullish else 'SELL'} @ {signal.reversal_time}")
                    elif sl_hit:
                        signal.status = 'SL_HIT'
                        signal.status_updated_at = hit_time
                        signal.save(update_fields=['status', 'status_updated_at'])
                        updated_count += 1
                        logger.info(f"❌ SL Hit: {symbol} {signal.timeframe} {'BUY' if signal.is_bullish else 'SELL'} @ {signal.reversal_time}")
                
            except Exception as e:
                logger.error(f"Error checking {symbol} signals: {e}")
                continue
        
        logger.info(f"✅ Status check complete: {checked_count} checked, {updated_count} updated")
        return {
            "status": "ok",
            "checked": checked_count,
            "updated": updated_count
        }
        
    except Exception as exc:
        logger.error(f"❌ Error in check_signal_statuses: {exc}")
        return {"status": "error", "error": str(exc)}