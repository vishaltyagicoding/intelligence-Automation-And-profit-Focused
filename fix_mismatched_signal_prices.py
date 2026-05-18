"""
fix_mismatched_signal_prices.py
================================
Run this ONCE on your server to fix all existing signal records whose
entry price (center_price) is the old pivot HIGH/LOW instead of the actual
candle close price at signal-confirmation time.

HOW IT WORKS
------------
1. Connects to Binance REST API to fetch historical kline (candle) data.
2. For every ReversalZone record in the DB, finds the actual CLOSE price of
   the candle at the signal's reversal_time.
3. Recalculates stop_loss and target from that real close price (same 2.5 R:R).
4. Updates center_price, stop_loss, target, outer_top, outer_bottom in the DB.

USAGE
-----
From your project root (where manage.py lives):

    python fix_mismatched_signal_prices.py

Or in dry-run mode (prints changes but does NOT write to DB):

    python fix_mismatched_signal_prices.py --dry-run

OPTIONS
-------
  --dry-run         Preview changes without touching the database.
  --symbol XAUUSD   Only fix one symbol (default: fix all).
  --days 30         How many days back to look (default: 60).
"""

import os
import sys
import django
import argparse
import requests
import logging
from datetime import datetime, timezone, timedelta
from decimal import Decimal

# ── Django setup ────────────────────────────────────────────────────────────
# Must be at the top so Django models are importable.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'neuraltrade.settings')
# If your settings module is different, change the line above.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from reversal_zones.models import ReversalZone   # noqa: E402  (after django.setup)

# ── Logging ─────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s  %(levelname)-8s  %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
log = logging.getLogger('price_fix')

# ── Binance symbol map ───────────────────────────────────────────────────────
# Maps the user-facing symbol stored in the DB → Binance REST symbol
SYMBOL_MAP = {
    'XAUUSD':  'PAXGUSDT',
    'BTCUSD':  'BTCUSDT',
    'ETHUSD':  'ETHUSDT',
    'LTCUSD':  'LTCUSDT',
    'BTCUSDT': 'BTCUSDT',
    'ETHUSDT': 'ETHUSDT',
    'LTCUSDT': 'LTCUSDT',
    'PAXGUSDT':'PAXGUSDT',
}

# Timeframe string → Binance interval
INTERVAL_MAP = {
    '1m': '1m',  '3m': '3m',  '5m': '5m',  '15m': '15m',
    '30m':'30m', '1h': '1h',  '4h': '4h',  '1d':  '1d',
    '1M': '1M',
    # aliases
    '5M': '5m', '15M': '15m', '1H': '1h', '4H': '4h',
}

BINANCE_BASE = 'https://api.binance.com/api/v3'
RR_RATIO     = 2.5   # risk-reward ratio (same as live signal engine)


# ── Helpers ──────────────────────────────────────────────────────────────────

def fetch_klines(binance_symbol: str, interval: str, start_ms: int, end_ms: int) -> list:
    """Fetch up to 1000 klines from Binance between start_ms and end_ms."""
    url    = f'{BINANCE_BASE}/klines'
    params = {
        'symbol':    binance_symbol,
        'interval':  interval,
        'startTime': start_ms,
        'endTime':   end_ms,
        'limit':     1000,
    }
    resp = requests.get(url, params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()   # list of lists: [open_time, O, H, L, C, V, close_time, ...]


def find_close_at(binance_symbol: str, interval: str, signal_dt: datetime) -> float | None:
    """
    Return the CLOSE price of the candle that CONTAINS signal_dt.
    Returns None if no matching candle is found.
    """
    signal_ms = int(signal_dt.timestamp() * 1000)
    # Search a small window: 5 candles before to 5 candles after
    interval_ms = interval_to_ms(interval)
    start_ms    = signal_ms - interval_ms * 3
    end_ms      = signal_ms + interval_ms * 3

    try:
        klines = fetch_klines(binance_symbol, interval, start_ms, end_ms)
    except Exception as exc:
        log.warning('  Binance fetch failed (%s %s @ %s): %s', binance_symbol, interval, signal_dt, exc)
        return None

    for k in klines:
        open_time_ms  = int(k[0])
        close_time_ms = int(k[6])
        if open_time_ms <= signal_ms <= close_time_ms:
            return float(k[4])   # index 4 = close price

    return None


def interval_to_ms(interval: str) -> int:
    """Convert interval string to milliseconds."""
    unit  = interval[-1].lower()
    count = int(interval[:-1])
    units = {'m': 60_000, 'h': 3_600_000, 'd': 86_400_000, 'w': 604_800_000}
    return count * units.get(unit, 60_000)


def recalculate(entry: float, sl: float, is_bull: bool) -> tuple[float, float, float, float, float]:
    """
    Given actual entry and the original SL (anchored to pivot structure),
    return (entry, sl, target, outer_top, outer_bottom).
    """
    risk = abs(entry - sl)
    if risk < entry * 0.001:
        risk = entry * 0.005   # 0.5% fallback guard

    target = round(entry + risk * RR_RATIO, 2) if is_bull else round(entry - risk * RR_RATIO, 2)
    sl     = round(sl,    2)
    entry  = round(entry, 2)

    outer_top    = round(target if is_bull else sl,    2)
    outer_bottom = round(sl     if is_bull else target, 2)

    return entry, sl, target, outer_top, outer_bottom


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='Fix mismatched signal prices in DB.')
    parser.add_argument('--dry-run', action='store_true',
                        help='Print changes but do NOT write to the database.')
    parser.add_argument('--symbol', default=None,
                        help='Only fix this symbol, e.g. XAUUSD  (default: all symbols).')
    parser.add_argument('--days', type=int, default=60,
                        help='How many days back to process (default: 60).')
    args = parser.parse_args()

    dry = args.dry_run
    if dry:
        log.info('═══ DRY-RUN MODE — no database changes will be made ═══')

    cutoff = datetime.now(tz=timezone.utc) - timedelta(days=args.days)

    qs = ReversalZone.objects.filter(reversal_time__gte=cutoff).order_by('reversal_time')
    if args.symbol:
        sym_upper = args.symbol.upper()
        # match both XAUUSD and PAXGUSDT variants
        qs = qs.filter(symbol__iexact=sym_upper) | \
             ReversalZone.objects.filter(
                 reversal_time__gte=cutoff,
                 symbol__iexact=SYMBOL_MAP.get(sym_upper, sym_upper)
             )
        qs = qs.distinct()

    total     = qs.count()
    updated   = 0
    skipped   = 0
    no_candle = 0

    log.info('Found %d signal records to check (last %d days).', total, args.days)

    for rec in qs:
        db_symbol  = rec.symbol.upper()
        binance_sym = SYMBOL_MAP.get(db_symbol, db_symbol)
        interval    = INTERVAL_MAP.get(rec.timeframe, rec.timeframe.lower())

        log.info(
            '── %s  %s  %s  %s  pivot=%.2f',
            rec.reversal_time.strftime('%Y-%m-%d %H:%M UTC'),
            db_symbol, rec.timeframe,
            'BUY' if rec.is_bullish else 'SELL',
            float(rec.center_price),
        )

        # Fetch actual close price at signal time from Binance
        actual_close = find_close_at(binance_sym, interval, rec.reversal_time)

        if actual_close is None:
            log.warning('  ⚠  No candle found on Binance — skipping.')
            no_candle += 1
            continue

        pivot_price = float(rec.center_price)

        # If entry is already very close to actual close, no fix needed
        if abs(pivot_price - actual_close) < actual_close * 0.0005:
            log.info('  ✓  Entry %.2f already matches close %.2f — no change needed.',
                     pivot_price, actual_close)
            skipped += 1
            continue

        # Get original SL (anchored to pivot structure)
        is_bull = rec.is_bullish
        if rec.stop_loss:
            orig_sl = float(rec.stop_loss)
        else:
            # Fallback: use outer_top/outer_bottom
            orig_sl = float(rec.outer_bottom) if is_bull else float(rec.outer_top)

        new_entry, new_sl, new_target, new_ot, new_ob = recalculate(
            actual_close, orig_sl, is_bull
        )

        log.info(
            '  → entry: %.2f → %.2f  |  SL: %.2f → %.2f  |  TP: %.2f → %.2f',
            pivot_price,    new_entry,
            orig_sl,        new_sl,
            float(rec.target) if rec.target else 0.0, new_target,
        )

        if not dry:
            rec.center_price  = Decimal(str(new_entry))
            rec.stop_loss     = Decimal(str(new_sl))
            rec.target        = Decimal(str(new_target))
            rec.outer_top     = Decimal(str(new_ot))
            rec.outer_bottom  = Decimal(str(new_ob))
            rec.save(update_fields=[
                'center_price', 'stop_loss', 'target',
                'outer_top', 'outer_bottom',
            ])

        updated += 1

    log.info('')
    log.info('══════════════════════════════════════════')
    log.info('Total records checked : %d', total)
    log.info('Records updated       : %d%s', updated, '  (dry-run — not saved)' if dry else '')
    log.info('Already correct       : %d', skipped)
    log.info('No Binance candle     : %d', no_candle)
    log.info('══════════════════════════════════════════')

    if dry and updated:
        log.info('Re-run WITHOUT --dry-run to apply these %d changes.', updated)


if __name__ == '__main__':
    main()