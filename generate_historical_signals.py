"""
Historical Signal Generator for SmartRisk
==========================================
This script regenerates historical signals using the EXACT trading logic from
the production system. It fetches real historical market data from Binance and
applies your ReversalZoneCalculator algorithm to generate legitimate signals.

KEY FEATURES:
- Uses ACTUAL trading logic (not random data)
- Fetches real historical market data
- Generates 100-200+ signals based on lookback period
- Updates signal statuses (TARGET_HIT, SL_HIT, OPEN)
- Safe to run multiple times (uses update_or_create)

USAGE:
  1. Upload to server: scp -i singapore-pem-file.pem generate_historical_signals.py ubuntu@52.221.219.7:~/smartrisk/
  2. SSH to server: ssh -i singapore-pem-file.pem ubuntu@52.221.219.7
  3. Run: cd ~/smartrisk && sudo docker-compose exec django python generate_historical_signals.py
  4. Wait 10-15 minutes for completion
"""

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'neuraltrade.settings')
django.setup()

import time
import pandas as pd
import requests as http_requests
import pytz
from datetime import datetime, timedelta

# ============================================================================
# CONFIGURATION - Adjust these to generate more/fewer signals
# ============================================================================

SYMBOLS = ["BTCUSDT", "ETHUSDT", "PAXGUSDT", "LTCUSDT"]
ALL_TIMEFRAMES = ["1m", "3m", "5m", "10m", "15m", "30m", "1h", "2h", "4h", "1d"]

# Binance API timeframe mapping (10m is aggregated from 5m)
BINANCE_TF = {
    "1m": "1m", "3m": "3m", "5m": "5m", "10m": "5m",
    "15m": "15m", "30m": "30m", "1h": "1h",
    "2h": "2h", "4h": "4h", "1d": "1d"
}

# INCREASED lookback periods to generate more signals
# Higher timeframes go back further to generate sufficient signal count
DAYS_BACK = {
    "1m": 7,      # ~10,080 candles → ~10-15 signals
    "3m": 21,     # ~10,080 candles → ~10-15 signals
    "5m": 30,     # ~8,640 candles → ~10-15 signals
    "10m": 45,    # ~6,480 candles → ~8-12 signals
    "15m": 60,    # ~5,760 candles → ~8-12 signals
    "30m": 90,    # ~4,320 candles → ~6-10 signals
    "1h": 120,    # ~2,880 candles → ~5-8 signals
    "2h": 180,    # ~2,160 candles → ~4-6 signals
    "4h": 240,    # ~1,440 candles → ~3-5 signals
    "1d": 365,    # ~365 candles → ~2-4 signals
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def fetch_historical_data(symbol, interval, days):
    """
    Fetch historical OHLCV data from Binance API.
    Returns pandas DataFrame with timestamp index and OHLC columns.
    """
    end_ts = int(time.time() * 1000)
    start_ts = int((time.time() - days * 86400) * 1000)
    
    all_rows = []
    current_ts = start_ts
    
    print(f"    Fetching {days} days of {interval} data from Binance...", end=" ", flush=True)
    
    while current_ts < end_ts:
        url = (
            f"https://api.binance.com/api/v3/klines"
            f"?symbol={symbol}&interval={interval}"
            f"&startTime={current_ts}&limit=1000"
        )
        
        try:
            resp = http_requests.get(url, timeout=15)
            resp.raise_for_status()
            batch = resp.json()
        except Exception as e:
            print(f"\n    ❌ Binance API error: {e}")
            break
        
        if not batch:
            break
        
        all_rows.extend(batch)
        current_ts = batch[-1][6] + 1  # Next timestamp
        
        if len(batch) < 1000:  # No more data available
            break
        
        time.sleep(0.25)  # Rate limiting
    
    if not all_rows:
        print("no data")
        return pd.DataFrame()
    
    print(f"{len(all_rows)} candles")
    
    # Convert to DataFrame
    df = pd.DataFrame(all_rows, columns=[
        "timestamp", "open", "high", "low", "close", "volume",
        "close_time", "qv", "trades", "tbb", "tbq", "ignore"
    ])
    
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
    
    for col in ["open", "high", "low", "close"]:
        df[col] = df[col].astype(float)
    
    df = df.set_index("timestamp")[["open", "high", "low", "close"]].sort_index()
    
    # Remove duplicates (keep last)
    df = df[~df.index.duplicated(keep="last")]
    
    return df


def aggregate_to_10m(df):
    """
    Aggregate 5-minute candles to 10-minute candles.
    Combines every 2 consecutive 5m candles.
    """
    rows = []
    times = []
    
    for i in range(0, len(df) - 1, 2):
        candle_a = df.iloc[i]
        candle_b = df.iloc[i + 1]
        
        rows.append({
            "open": float(candle_a["open"]),
            "high": max(float(candle_a["high"]), float(candle_b["high"])),
            "low": min(float(candle_a["low"]), float(candle_b["low"])),
            "close": float(candle_b["close"])
        })
        times.append(df.index[i])
    
    return pd.DataFrame(rows, index=times)


def save_signals_to_db(symbol, timeframe, zones):
    """
    Save generated signals to database.
    Uses update_or_create to avoid duplicates.
    """
    from reversal_zones.models import ReversalZone
    from django.db import IntegrityError
    
    saved_count = 0
    
    for zone in zones:
        try:
            # Extract timestamp
            ts = zone.get("timestamp") or zone.get("reversal_time")
            
            if isinstance(ts, str):
                from django.utils.dateparse import parse_datetime
                reversal_time = parse_datetime(ts)
            elif hasattr(ts, "to_pydatetime"):
                reversal_time = ts.to_pydatetime()
            else:
                reversal_time = ts
            
            if reversal_time is None:
                continue
            
            # Ensure timezone aware
            if reversal_time.tzinfo is None:
                reversal_time = pytz.utc.localize(reversal_time)
            
            is_bullish = zone.get("is_bullish", True)
            
            # Create or update signal
            obj, created = ReversalZone.objects.update_or_create(
                symbol=symbol,
                timeframe=timeframe,
                reversal_time=reversal_time,
                defaults={
                    "center_price": zone["center_price"],
                    "stop_loss": zone.get("stop_loss"),
                    "target": zone.get("target"),
                    "outer_top": zone["outer_top"],
                    "outer_bottom": zone["outer_bottom"],
                    "core_top": zone["core_top"],
                    "core_bottom": zone["core_bottom"],
                    "is_bullish": is_bullish,
                    "label_text": "BUY" if is_bullish else "SELL",
                    "status": "OPEN",  # Will be updated by status check task
                }
            )
            
            # Set bar_index only on first creation
            if created:
                obj.bar_index = zone.get("bar_index", 0)
                obj.save(update_fields=["bar_index"])
                saved_count += 1
        
        except IntegrityError as e:
            # Skip alternation constraint errors (should not happen with new logic)
            if "Consecutive" not in str(e):
                print(f"\n    ⚠️  DB error: {e}")
        except Exception as e:
            print(f"\n    ⚠️  Save error: {e}")
    
    return saved_count


def update_signal_statuses():
    """
    Update signal statuses (OPEN → TARGET_HIT or SL_HIT) based on historical price data.
    This is called after all signals are generated.
    """
    from reversal_zones.tasks import check_signal_statuses
    
    print("\n" + "=" * 80)
    print("STEP 2: Updating signal statuses (TARGET_HIT, SL_HIT, OPEN)")
    print("=" * 80)
    print("\nThis will check all OPEN signals against historical price data...")
    print("Expected time: 2-5 minutes\n")
    
    try:
        check_signal_statuses()
        print("\n✅ Signal statuses updated successfully!")
    except Exception as e:
        print(f"\n⚠️  Status update error: {e}")
        print("You can manually run: python manage.py update_signal_statuses")


# ============================================================================
# MAIN SIGNAL GENERATION
# ============================================================================

def generate_all_historical_signals():
    """
    Main function to generate historical signals for all symbols and timeframes.
    """
    from reversal_zones.reversal_calculator import ReversalZoneCalculator
    
    print("=" * 80)
    print("SmartRisk Historical Signal Generator")
    print("=" * 80)
    print(f"\nStarted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\nGenerating signals for:")
    print(f"  - Symbols: {', '.join(SYMBOLS)}")
    print(f"  - Timeframes: {', '.join(ALL_TIMEFRAMES)}")
    print(f"  - Total combinations: {len(SYMBOLS) * len(ALL_TIMEFRAMES)}")
    print(f"\nEstimated time: 10-15 minutes")
    print(f"Expected output: 100-300 signals (depending on market conditions)")
    print("\n" + "=" * 80)
    print("STEP 1: Generating signals using EXACT trading logic")
    print("=" * 80 + "\n")
    
    total_saved = 0
    total_generated = 0
    
    for symbol in SYMBOLS:
        print(f"\n📊 Processing {symbol}...")
        
        for tf in ALL_TIMEFRAMES:
            days = DAYS_BACK[tf]
            print(f"  [{tf:>4}] ", end="", flush=True)
            
            # Fetch historical data
            df = fetch_historical_data(symbol, BINANCE_TF[tf], days)
            
            if df.empty or len(df) < 20:
                print("    ❌ Insufficient data")
                continue
            
            # Aggregate to 10m if needed
            if tf == "10m":
                df = aggregate_to_10m(df)
            
            try:
                # Initialize calculator with EXACT production settings
                calculator = ReversalZoneCalculator(
                    preset="Low",
                    calc_mode="Average",
                    avg_len=5,
                    atr_len=5,
                    custom_abs=0.05,
                    confirm_bars=0,  # No extra confirmation delay
                    timeframe=tf
                )
                
                # Drop last (open/live) candle — only closed bars
                if len(df) > 1:
                    df = df.iloc[:-1]
                
                # Generate signals using ACTUAL trading logic
                result = calculator.process_ohlcv_data(df)
                zones = result.get("zones", [])
                
                # Save to database
                saved = save_signals_to_db(symbol, tf, zones)
                
                total_generated += len(zones)
                total_saved += saved
                
                print(f"    ✅ {len(zones)} signals generated → {saved} new saved")
            
            except Exception as e:
                print(f"    ❌ Error: {e}")
    
    print("\n" + "=" * 80)
    print("GENERATION SUMMARY")
    print("=" * 80)
    print(f"Total signals generated: {total_generated}")
    print(f"Total NEW signals saved: {total_saved}")
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80 + "\n")
    
    return total_saved


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    try:
        # Step 1: Generate signals
        total_signals = generate_all_historical_signals()
        
        # Step 2: Update statuses
        if total_signals > 0:
            update_signal_statuses()
        
        print("\n" + "=" * 80)
        print("✅ HISTORICAL SIGNAL GENERATION COMPLETE!")
        print("=" * 80)
        print("\nNext steps:")
        print("  1. Visit https://smartriskfx.com/history to view signals")
        print("  2. Check charts - signals should appear at reversal zones")
        print("  3. Verify signal statuses (TARGET_HIT, SL_HIT, OPEN)")
        print("\nAll signals are based on ACTUAL trading logic, not random data!")
        print("=" * 80 + "\n")
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Process interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
