"""
fix_mismatched_signal_prices.py
================================
Backfills stop_loss and target for all old ReversalZone records where
those fields are NULL.

NO external API calls needed — all data is already in your database.
Works on AWS even when Binance API is geo-blocked (HTTP 451).

HOW IT WORKS
------------
Old records were saved before the consumers.py fix. They have:
  - center_price  ✓ (entry price — already correct)
  - outer_top     ✓ (already in DB)
  - outer_bottom  ✓ (already in DB)
  - stop_loss     ✗ NULL  ← needs filling
  - target        ✗ NULL  ← needs filling

For a SELL signal:  stop_loss = outer_top,    target = outer_bottom
For a BUY  signal:  stop_loss = outer_bottom, target = outer_top

USAGE (inside your Docker container)
--------------------------------------
    python fix_mismatched_signal_prices.py --dry-run   # preview only
    python fix_mismatched_signal_prices.py             # apply all
    python fix_mismatched_signal_prices.py --symbol PAXGUSDT
    python fix_mismatched_signal_prices.py --days 30
    python fix_mismatched_signal_prices.py --all       # every record ever
"""

import os, sys, django, argparse, logging
from datetime import datetime, timezone, timedelta
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'neuraltrade.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from reversal_zones.models import ReversalZone

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s  %(levelname)-8s  %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
log = logging.getLogger('price_fix')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run',  action='store_true')
    parser.add_argument('--symbol',   default=None)
    parser.add_argument('--days',     type=int, default=90)
    parser.add_argument('--all',      dest='fix_all', action='store_true',
                        help='Process every record regardless of date')
    args = parser.parse_args()

    dry = args.dry_run
    if dry:
        log.info('═══ DRY-RUN — no DB writes ═══')

    qs = ReversalZone.objects.all()
    if not args.fix_all:
        cutoff = datetime.now(tz=timezone.utc) - timedelta(days=args.days)
        qs = qs.filter(reversal_time__gte=cutoff)
    if args.symbol:
        qs = qs.filter(symbol__iexact=args.symbol.upper())
    qs = qs.order_by('reversal_time')

    total = qs.count()
    fixed_null = mismatched = already_ok = errors = 0
    batch = []

    log.info('Scanning %d records...', total)

    for rec in qs.iterator(chunk_size=500):
        is_bull   = rec.is_bullish
        outer_top = rec.outer_top
        outer_bot = rec.outer_bottom

        if outer_top is None or outer_bot is None:
            log.warning('SKIP %s %s %s — outer values missing',
                        rec.reversal_time.strftime('%Y-%m-%d %H:%M'),
                        rec.symbol, rec.timeframe)
            errors += 1
            continue

        # SELL → SL = outer_top (above entry), TP = outer_bottom (below entry)
        # BUY  → SL = outer_bottom (below entry), TP = outer_top (above entry)
        correct_sl  = outer_bot if is_bull else outer_top
        correct_tgt = outer_top if is_bull else outer_bot

        cur_sl  = rec.stop_loss
        cur_tgt = rec.target

        if cur_sl is None or cur_tgt is None:
            reason = 'NULL → filled'
            fixed_null += 1
        elif (abs(float(cur_sl) - float(correct_sl)) > 0.001 or
              abs(float(cur_tgt) - float(correct_tgt)) > 0.001):
            reason = f'MISMATCH (was SL={cur_sl} TP={cur_tgt})'
            mismatched += 1
        else:
            already_ok += 1
            continue

        log.info('%s %s %-6s %-4s  entry=%-12s  SL: %-12s→ %-12s  TP: %-12s→ %s  [%s]',
                 rec.symbol,
                 rec.reversal_time.strftime('%Y-%m-%d %H:%M'),
                 rec.timeframe,
                 'BUY' if is_bull else 'SELL',
                 str(rec.center_price),
                 str(cur_sl), str(correct_sl),
                 str(cur_tgt), str(correct_tgt),
                 reason)

        if not dry:
            rec.stop_loss = Decimal(str(correct_sl))
            rec.target    = Decimal(str(correct_tgt))
            batch.append(rec)
            if len(batch) >= 200:
                ReversalZone.objects.bulk_update(batch, ['stop_loss', 'target'])
                log.info('  ... saved batch of %d', len(batch))
                batch.clear()

    if not dry and batch:
        ReversalZone.objects.bulk_update(batch, ['stop_loss', 'target'])
        log.info('  ... saved final batch of %d', len(batch))

    total_fixed = fixed_null + mismatched
    log.info('')
    log.info('══════════════════════════════════════════')
    log.info('Total scanned      : %d', total)
    log.info('NULL SL/TP filled  : %d%s', fixed_null,
             ' (dry-run — NOT saved)' if dry else ' ✅')
    log.info('Mismatched fixed   : %d%s', mismatched,
             ' (dry-run — NOT saved)' if dry else ' ✅')
    log.info('Already correct    : %d', already_ok)
    log.info('Skipped (no data)  : %d', errors)
    log.info('══════════════════════════════════════════')
    log.info('TOTAL FIXED        : %d', total_fixed)

    if dry and total_fixed:
        log.info('')
        log.info('Re-run WITHOUT --dry-run to save these %d changes.', total_fixed)

    if not dry and total_fixed:
        log.info('')
        log.info('Verify with:')
        log.info('  python manage.py shell -c "'
                 'from reversal_zones.models import ReversalZone; '
                 'n=ReversalZone.objects.filter(stop_loss__isnull=True).count(); '
                 'print(f\'NULL stop_loss remaining: {n}\')"')


if __name__ == '__main__':
    main()