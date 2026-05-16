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

ALL_TIMEFRAMES = ["1m", "3m", "5m", "10m", "15m", "30m", "1h", "2h", "4h", "1d"]

BINANCE_TF = {
    "1m": "1m", "3m": "3m", "5m": "5m", "10m": "5m",
    "15m": "15m", "30m": "30m", "1h": "1h",
    "2h": "2h", "4h": "4h", "1d": "1d",
}

# Full history window per timeframe (daily full recalculation)
DAYS_BACK = {
    "1m": 7,   "3m": 14,  "5m": 21,  "10m": 30,
    "15m": 30, "30m": 30, "1h": 30,
    "2h": 30,  "4h": 30,  "1d": 30,
}

# Recent window for 30-min incremental updates (hours)
RECENT_HOURS = {
    "1m": 6,   "3m": 12,  "5m": 24,  "10m": 48,
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
    Bulk-save filtered zones to DB.
    Uses update_or_create on (symbol, timeframe, reversal_time).
    Returns count of newly created records.
    """
    from reversal_zones.models import ReversalZone
    from django.db import IntegrityError

    saved = 0
    new_signals = []  # Track new signals for email notifications
    
    for z in zones:
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
                    "label_text":   "BUY" if is_bull else "SELL",
                    "bar_index":    z.get("bar_index", 0),
                },
            )
            if created:
                saved += 1
                # Store signal data for email notification
                new_signals.append({
                    'zone': zone,
                    'data': z
                })

        except (IntegrityError, Exception) as e:
            msg = str(e)
            if "Consecutive" in msg and "signals not allowed" in msg:
                logger.info("🛡️ DB constraint blocked consecutive signal [%s %s]", symbol, timeframe)
            else:
                logger.error("Error saving zone [%s %s]: %s", symbol, timeframe, e)

    # Send email notifications for new signals (only paid subscribers)
    if new_signals:
        _send_signal_notifications(symbol, timeframe, new_signals)

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


def _send_signal_notifications(symbol: str, timeframe: str, new_signals: list):
    """
    Send email notifications to paid subscribers for new signals.
    Converts internal Binance symbol (BTCUSDT) to user-facing symbol (BTCUSD).
    Only sends to users with manual_subscription='activated'.

    CRITICAL: entry/stop_loss/target are rounded to 2 decimal places so the
    email alert and the history page always show identical values.
    """
    try:
        from signal_alerts.email_utils import notify_signal_subscribers
        import pytz

        # Convert Binance format (BTCUSDT) → user-facing format (BTCUSD)
        user_symbol = _BINANCE_TO_USER_SYMBOL.get(symbol.upper(), symbol)

        for signal_info in new_signals:
            zone = signal_info['zone']

            is_bull    = zone.is_bullish
            entry      = round(float(zone.center_price), 2)
            outer_top  = round(float(zone.outer_top),    2)
            outer_bot  = round(float(zone.outer_bottom), 2)

            # BUY:  stop_loss = outer_bottom (below entry), target = outer_top (above entry)
            # SELL: stop_loss = outer_top    (above entry), target = outer_bottom (below entry)
            if is_bull:
                stop_loss = outer_bot
                target    = outer_top
            else:
                stop_loss = outer_top
                target    = outer_bot

            ts_str = zone.reversal_time.astimezone(pytz.utc).strftime('%Y-%m-%d %H:%M:%S UTC')

            signal_data = {
                'crypto':       user_symbol,   # BTCUSD / ETHUSD / XAUUSD / LTCUSD
                'timeframe':    timeframe,
                'signal_type':  'BUY' if is_bull else 'SELL',
                'entry_price':  entry,
                'target':       target,
                'stop_loss':    stop_loss,
                'timestamp':    ts_str,
            }

            notifications_sent = notify_signal_subscribers(signal_data)

            if notifications_sent > 0:
                logger.info(
                    "📧 %d email(s) sent — %s %s %s  Entry=%.2f  SL=%.2f  TP=%.2f",
                    notifications_sent, user_symbol, timeframe,
                    signal_data['signal_type'], entry, stop_loss, target,
                )

    except Exception as e:
        logger.error("Error sending signal notifications: %s", e, exc_info=True)


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

        if timeframe == "10m":
            df = _aggregate_10m(df)

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
    Runs every 30 minutes for all 4 symbols × 10 timeframes = 40 tasks.
    """
    from reversal_zones.signal_filter import AntiChopFilter

    binance_tf = BINANCE_TF.get(timeframe, "1h")
    hours_back = RECENT_HOURS.get(timeframe, 48)

    try:
        last_db = _get_last_db_signal(symbol, timeframe)

        df = _fetch_binance_recent(symbol, binance_tf, hours_back)
        if df.empty or len(df) < 20:
            return {"status": "no_data"}

        if timeframe == "10m":
            df = _aggregate_10m(df)

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
    Runs every 30 minutes — this is what makes Pine Script logic
    work continuously throughout the day.
    """
    logger.info("🔄 30-min incremental signal update starting...")
    count = 0
    for symbol in SYMBOLS:
        for tf in ALL_TIMEFRAMES:
            update_recent_signals_for_symbol_timeframe.apply_async(
                args=[symbol, tf],
                countdown=count * 1,
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