import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'neuraltrade.settings')
django.setup()

import time
import pandas as pd
import requests as http_requests
import pytz

SYMBOLS    = ["BTCUSDT", "ETHUSDT", "PAXGUSDT", "LTCUSDT"]
ALL_TF     = ["1m","3m","5m","10m","15m","30m","1h","2h","4h","1d"]
BINANCE_TF = {"1m":"1m","3m":"3m","5m":"5m","10m":"5m",
              "15m":"15m","30m":"30m","1h":"1h",
              "2h":"2h","4h":"4h","1d":"1d"}
DAYS_BACK  = {"1m":7,"3m":14,"5m":21,"10m":30,
              "15m":30,"30m":30,"1h":30,
              "2h":30,"4h":30,"1d":30}

def fetch(symbol, interval, days):
    end_ts   = int(time.time() * 1000)
    start_ts = int((time.time() - days * 86400) * 1000)
    rows, current = [], start_ts
    while current < end_ts:
        url = (f"https://api.binance.com/api/v3/klines"
               f"?symbol={symbol}&interval={interval}"
               f"&startTime={current}&limit=1000")
        try:
            resp = http_requests.get(url, timeout=15)
            resp.raise_for_status()
            batch = resp.json()
        except Exception as e:
            print(f"  Binance error: {e}"); break
        if not batch: break
        rows.extend(batch)
        current = batch[-1][6] + 1
        if len(batch) < 1000: break
        time.sleep(0.25)
    if not rows: return pd.DataFrame()
    df = pd.DataFrame(rows, columns=[
        "timestamp","open","high","low","close","volume",
        "close_time","qv","trades","tbb","tbq","ignore"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
    for c in ["open","high","low","close"]:
        df[c] = df[c].astype(float)
    df = df.set_index("timestamp")[["open","high","low","close"]].sort_index()
    return df[~df.index.duplicated(keep="last")]

def agg_10m(df):
    rows, times = [], []
    for i in range(0, len(df)-1, 2):
        a, b = df.iloc[i], df.iloc[i+1]
        rows.append({"open":float(a["open"]),
                     "high":max(float(a["high"]),float(b["high"])),
                     "low": min(float(a["low"]), float(b["low"])),
                     "close":float(b["close"])})
        times.append(df.index[i])
    return pd.DataFrame(rows, index=times)

def save_zones(symbol, timeframe, zones):
    from reversal_zones.models import ReversalZone
    from django.db import IntegrityError
    saved = 0
    for z in zones:
        try:
            ts = z.get("timestamp") or z.get("reversal_time")
            if isinstance(ts, str):
                from django.utils.dateparse import parse_datetime
                rt = parse_datetime(ts)
            elif hasattr(ts, "to_pydatetime"):
                rt = ts.to_pydatetime()
            else:
                rt = ts
            if rt is None: continue
            if rt.tzinfo is None: rt = pytz.utc.localize(rt)
            is_bull = z.get("is_bullish", True)
            obj, created = ReversalZone.objects.update_or_create(
                symbol=symbol, timeframe=timeframe, reversal_time=rt,
                defaults={
                    "center_price": z["center_price"],
                    # stop_loss and target from calculator ATR-based logic
                    # (1.0×ATR for SL, 2.0×ATR for Target, 1:2 RR).
                    # These are the SINGLE SOURCE OF TRUTH for SL/Target values.
                    # History page, live chart, and email notifications all read
                    # these fields from the DB — so they are always identical.
                    "stop_loss":    z.get("stop_loss"),
                    "target":       z.get("target"),
                    "outer_top":    z["outer_top"],
                    "outer_bottom": z["outer_bottom"],
                    "core_top":     z["core_top"],
                    "core_bottom":  z["core_bottom"],
                    "is_bullish":   is_bull,
                    "label_text":   "BUY" if is_bull else "SELL",
                    # bar_index excluded — relative window offset, shifts on every run.
                    # Set once on first insert only (see below).
                },
            )
            if created:
                obj.bar_index = z.get("bar_index", 0)
                obj.save(update_fields=["bar_index"])
                saved += 1
        except (IntegrityError, Exception) as e:
            if "Consecutive" not in str(e):
                print(f"    Save error: {e}")
    return saved

from reversal_zones.reversal_calculator import ReversalZoneCalculator

total_saved = 0
for symbol in SYMBOLS:
    for tf in ALL_TF:
        days = DAYS_BACK[tf]
        print(f"-> {symbol} {tf} ({days}d)...", end=" ", flush=True)
        df = fetch(symbol, BINANCE_TF[tf], days)
        if df.empty or len(df) < 20:
            print("no data"); continue
        if tf == "10m": df = agg_10m(df)
        try:
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
                confirm_bars=0,  # Pine Script default: 0 (no extra delay) — matches TradingView exactly
                timeframe=tf
            )
            # Drop last (open/live) candle — only process closed bars
            if len(df) > 1:
                df = df.iloc[:-1]

            result = calculator.process_ohlcv_data(df)
            zones = result.get("zones", [])
            saved = save_zones(symbol, tf, zones)
            total_saved += saved
            print(f"{len(df)} candles -> {len(zones)} signals -> {saved} new saved")
        except Exception as e:
            print(f"ERROR: {e}")

print(f"\nBackfill done. Total new signals saved: {total_saved}")