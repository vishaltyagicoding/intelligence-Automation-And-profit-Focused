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

# Recent window for 60-second incremental updates (hours).
# Must be large enough for calculator EMA warmup (~25 bars minimum)
# but small enough to finish quickly.
# 5M:  4h = 48 candles  (EMA-5 needs 25, we give 48 for safety)
# 15M: 6h = 24 candles
# 30M: 12h = 24 candles
# 1H:  24h = 24 candles
# 2H:  48h = 24 candles
# 4H:  96h = 24 candles
# 1D:  30d = 30 candles
RECENT_HOURS = {
    "5m":  4,
    "15m": 6,  "30m": 12, "1h": 24,
    "2h":  48, "4h":  96, "1d": 720,
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
                        "bar_index":    z.get("bar_index", 0),
                    },
                )
                if created:
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
    from reversal_zones.signal_filter import AntiChopFilter

    binance_tf = BINANCE_TF.get(timeframe, "1h")
    days_back  = DAYS_BACK.get(timeframe, 30)

    logger.info("📊 Full history: %s %s (%d days)", symbol, timeframe, days_back)

    try:
        df = _fetch_binance_paginated(symbol, binance_tf, days_back)

        if df.empty or len(df) < 20:
            logger.warning("Not enough data: %s %s", symbol, timeframe)
            return {"status": "no_data"}

        result = AntiChopFilter(timeframe=timeframe).process(df, symbol=symbol, check_db=True)
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

        # Pass symbol so AntiChopFilter seeds last_signal from DB
        # This ensures correct BUY→SELL alternation across task runs
        result    = AntiChopFilter(timeframe=timeframe).process(df, symbol=symbol, check_db=True)
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