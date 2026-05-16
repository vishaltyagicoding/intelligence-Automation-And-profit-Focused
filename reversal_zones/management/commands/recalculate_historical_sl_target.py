"""
Django management command to recalculate ALL historical stop loss and target values.

This command fetches historical OHLCV data from Binance and recalculates professional
stop loss and target for EVERY existing signal in the database using the swing-based logic.

Usage:
    python manage.py recalculate_historical_sl_target
    python manage.py recalculate_historical_sl_target --symbol BTCUSDT
    python manage.py recalculate_historical_sl_target --timeframe 5m
    python manage.py recalculate_historical_sl_target --dry-run
"""

from django.core.management.base import BaseCommand
from reversal_zones.models import ReversalZone
from reversal_zones.reversal_calculator import _professional_sl_target, _atr
import requests
import pandas as pd
import time
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Recalculate historical stop loss and target values using professional logic'

    def add_arguments(self, parser):
        parser.add_argument(
            '--symbol',
            type=str,
            help='Specific symbol to update (e.g., BTCUSDT). If not provided, updates all symbols.'
        )
        parser.add_argument(
            '--timeframe',
            type=str,
            help='Specific timeframe to update (e.g., 5m). If not provided, updates all timeframes.'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Limit number of records to update (for testing)'
        )

    def handle(self, *args, **options):
        symbol_filter = options.get('symbol')
        timeframe_filter = options.get('timeframe')
        dry_run = options.get('dry_run')
        limit = options.get('limit')

        self.stdout.write(self.style.SUCCESS(
            f'\n{"="*80}\n'
            f'RECALCULATING HISTORICAL STOP LOSS & TARGET VALUES\n'
            f'{"="*80}\n'
            f'Symbol:    {symbol_filter or "ALL"}\n'
            f'Timeframe: {timeframe_filter or "ALL"}\n'
            f'Dry Run:   {dry_run}\n'
            f'Limit:     {limit or "No limit"}\n'
            f'{"="*80}\n'
        ))

        # Build query
        query = ReversalZone.objects.all()
        if symbol_filter:
            query = query.filter(symbol=symbol_filter.upper())
        if timeframe_filter:
            query = query.filter(timeframe=timeframe_filter.lower())
        
        query = query.order_by('symbol', 'timeframe', 'reversal_time')
        
        if limit:
            query = query[:limit]

        total_count = query.count()
        self.stdout.write(f'Found {total_count} records to process...\n')

        if total_count == 0:
            self.stdout.write(self.style.WARNING('No records found. Exiting.'))
            return

        # Group by symbol + timeframe to minimize API calls
        grouped = {}
        for record in query:
            key = (record.symbol, record.timeframe)
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(record)

        self.stdout.write(f'Processing {len(grouped)} symbol/timeframe combinations...\n')

        updated_count = 0
        error_count = 0

        for (symbol, timeframe), records in grouped.items():
            self.stdout.write(f'\n📊 Processing {symbol} {timeframe} ({len(records)} signals)...')
            
            try:
                # Fetch OHLCV data from Binance
                df = self._fetch_binance_data(symbol, timeframe)
                
                if df is None or df.empty:
                    self.stdout.write(self.style.ERROR(f'  ❌ Failed to fetch data for {symbol} {timeframe}'))
                    error_count += len(records)
                    continue

                # Calculate ATR series
                atr_series = _atr(df['high'], df['low'], df['close'], length=14)

                # Process each record
                for record in records:
                    try:
                        # Find the bar index closest to the signal time
                        bar_index = self._find_bar_index(df, record.reversal_time)
                        
                        if bar_index is None:
                            self.stdout.write(self.style.WARNING(
                                f'  ⚠️  Could not find bar for {record.reversal_time}'
                            ))
                            error_count += 1
                            continue

                        # Get ATR at signal bar
                        atr_val = float(atr_series.iloc[bar_index]) if bar_index < len(atr_series) else abs(float(record.center_price)) * 0.002

                        # Calculate professional stop loss and target
                        stop_loss, target = _professional_sl_target(
                            df=df,
                            bar_index=bar_index,
                            center_price=float(record.center_price),
                            is_bullish=record.is_bullish,
                            atr_now=atr_val,
                            timeframe=timeframe,
                        )

                        # Get old values for comparison
                        old_stop = float(record.outer_bottom if record.is_bullish else record.outer_top)
                        old_target = float(record.outer_top if record.is_bullish else record.outer_bottom)

                        # Update database
                        if not dry_run:
                            if record.is_bullish:
                                record.outer_bottom = Decimal(str(round(stop_loss, 2)))
                                record.outer_top = Decimal(str(round(target, 2)))
                            else:
                                record.outer_top = Decimal(str(round(stop_loss, 2)))
                                record.outer_bottom = Decimal(str(round(target, 2)))
                            
                            record.save(update_fields=['outer_top', 'outer_bottom'])
                            updated_count += 1

                        # Show progress every 10 records
                        if (updated_count + 1) % 10 == 0 or dry_run:
                            action = 'Would update' if dry_run else 'Updated'
                            self.stdout.write(
                                f'  {action} {record.label_text} @ {float(record.center_price):.2f} | '
                                f'SL: {old_stop:.2f} → {stop_loss:.2f} | '
                                f'TP: {old_target:.2f} → {target:.2f}'
                            )

                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'  ❌ Error processing record: {e}'))
                        error_count += 1
                        continue

                self.stdout.write(self.style.SUCCESS(f'  ✅ Completed {symbol} {timeframe}'))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ❌ Error processing {symbol} {timeframe}: {e}'))
                error_count += len(records)
                continue

        # Final summary
        self.stdout.write(self.style.SUCCESS(
            f'\n{"="*80}\n'
            f'{"DRY RUN " if dry_run else ""}COMPLETE\n'
            f'{"="*80}\n'
            f'Total records:   {total_count}\n'
            f'Updated:         {updated_count}\n'
            f'Errors:          {error_count}\n'
            f'{"="*80}\n'
        ))

        if dry_run:
            self.stdout.write(self.style.WARNING(
                '\n⚠️  DRY RUN MODE - No changes were saved to database\n'
                'Run without --dry-run to apply changes\n'
            ))

    def _fetch_binance_data(self, symbol, timeframe):
        """Fetch OHLCV data from Binance for the last 60 days"""
        TF_MAP = {
            '5m': '5m',
            '15m': '15m', '30m': '30m', '1h': '1h', '2h': '2h',
            '4h': '4h', '1d': '1d',
        }
        binance_tf = TF_MAP.get(timeframe, '1h')
        
        # Fetch last 60 days of data
        end_ts = int(time.time() * 1000)
        start_ts = int((time.time() - 60 * 86400) * 1000)
        
        all_rows = []
        current = start_ts
        limit = 1000

        while current < end_ts:
            url = (
                f"https://api.binance.us/api/v3/klines"
                f"?symbol={symbol}&interval={binance_tf}"
                f"&startTime={current}&limit={limit}"
            )
            
            try:
                resp = requests.get(url, timeout=15)
                resp.raise_for_status()
                batch = resp.json()
            except Exception as e:
                logger.error(f"Binance fetch error [{symbol} {binance_tf}]: {e}")
                return None

            if not batch:
                break

            all_rows.extend(batch)
            current = batch[-1][6] + 1  # next start = close_time + 1ms

            if len(batch) < limit:
                break

            time.sleep(0.25)  # Rate limiting

        if not all_rows:
            return None

        df = pd.DataFrame(all_rows, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'qv', 'trades', 'tbb', 'tbq', 'ignore'
        ])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
        for col in ['open', 'high', 'low', 'close']:
            df[col] = df[col].astype(float)
        df = df.set_index('timestamp')[['open', 'high', 'low', 'close']].sort_index()
        df = df[~df.index.duplicated(keep='last')]

        return df

    def _aggregate_10m(self, df):
        """Aggregate consecutive 5m candle pairs into 10m candles"""
        rows, times = [], []
        for i in range(0, len(df) - 1, 2):
            a, b = df.iloc[i], df.iloc[i + 1]
            rows.append({
                'open': float(a['open']),
                'high': max(float(a['high']), float(b['high'])),
                'low': min(float(a['low']), float(b['low'])),
                'close': float(b['close']),
            })
            times.append(df.index[i])
        return pd.DataFrame(rows, index=times)

    def _find_bar_index(self, df, signal_time):
        """Find the bar index in df closest to signal_time"""
        try:
            # Convert signal_time to timezone-aware if needed
            if signal_time.tzinfo is None:
                import pytz
                signal_time = pytz.utc.localize(signal_time)
            
            # Find closest timestamp
            time_diffs = abs(df.index - signal_time)
            closest_idx = time_diffs.argmin()
            
            # Verify it's within reasonable range (1 hour)
            # time_diffs is a TimedeltaIndex, use [closest_idx] not .iloc[]
            if time_diffs[closest_idx].total_seconds() > 3600:
                return None
            
            return closest_idx
        except Exception as e:
            logger.error(f"Error finding bar index: {e}")
            return None
