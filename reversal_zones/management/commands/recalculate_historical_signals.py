"""
Django management command to recalculate stop loss and target values
for all historical signals using the new universal calculation logic.

Usage:
    python manage.py recalculate_historical_signals
    python manage.py recalculate_historical_signals --symbol BTCUSD
    python manage.py recalculate_historical_signals --timeframe 15m
    python manage.py recalculate_historical_signals --dry-run
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from reversal_zones.models import ReversalZone
from reversal_zones.reversal_calculator import _professional_sl_target
import pandas as pd
import requests
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


# Symbol mapping: User symbols → Binance symbols
_USER_TO_BINANCE_SYMBOL = {
    'XAUUSD':  'PAXGUSDT',
    'BTCUSD':  'BTCUSDT',
    'ETHUSD':  'ETHUSDT',
    'LTCUSD':  'LTCUSDT',
}


class Command(BaseCommand):
    help = 'Recalculate stop loss and target values for historical signals'

    def add_arguments(self, parser):
        parser.add_argument(
            '--symbol',
            type=str,
            help='Recalculate only for specific symbol (e.g., BTCUSD, XAUUSD)',
        )
        parser.add_argument(
            '--timeframe',
            type=str,
            help='Recalculate only for specific timeframe (e.g., 15m, 1h, 4h)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview changes without saving to database',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Limit number of records to process (for testing)',
        )

    def handle(self, *args, **options):
        symbol = options.get('symbol')
        timeframe = options.get('timeframe')
        dry_run = options.get('dry_run')
        limit = options.get('limit')

        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(self.style.SUCCESS('Universal Stop Loss & Target Recalculation'))
        self.stdout.write(self.style.SUCCESS('=' * 80))

        # Build query
        queryset = ReversalZone.objects.all().order_by('-reversal_time')
        
        if symbol:
            # Convert user symbol to Binance symbol for database query
            db_symbol = _USER_TO_BINANCE_SYMBOL.get(symbol, symbol)
            queryset = queryset.filter(symbol=db_symbol)
            self.stdout.write(f"Filtering by symbol: {symbol} (DB: {db_symbol})")
        
        if timeframe:
            queryset = queryset.filter(timeframe=timeframe)
            self.stdout.write(f"Filtering by timeframe: {timeframe}")
        
        if limit:
            queryset = queryset[:limit]
            self.stdout.write(f"Limiting to {limit} records")

        total_count = queryset.count()
        self.stdout.write(f"\nTotal records to process: {total_count}")
        
        if dry_run:
            self.stdout.write(self.style.WARNING("\n🔍 DRY RUN MODE - No changes will be saved\n"))
        else:
            self.stdout.write(self.style.WARNING("\n⚠️  LIVE MODE - Changes will be saved to database\n"))

        # Process records
        success_count = 0
        error_count = 0
        skipped_count = 0

        for idx, record in enumerate(queryset, 1):
            try:
                # Progress indicator
                if idx % 10 == 0:
                    self.stdout.write(f"Processing {idx}/{total_count}...")

                # Fetch historical OHLCV data from Binance
                df = self._fetch_ohlcv_data(
                    symbol=record.symbol,
                    timeframe=record.timeframe,
                    reversal_time=record.reversal_time,
                )

                if df is None or len(df) < 50:
                    self.stdout.write(
                        self.style.WARNING(
                            f"⚠️  Skipped {record.symbol} {record.timeframe} @ {record.reversal_time} "
                            f"- insufficient data"
                        )
                    )
                    skipped_count += 1
                    continue

                # Find the bar index closest to reversal_time
                bar_index = self._find_bar_index(df, record.reversal_time)
                
                if bar_index < 0 or bar_index >= len(df):
                    self.stdout.write(
                        self.style.WARNING(
                            f"⚠️  Skipped {record.symbol} {record.timeframe} @ {record.reversal_time} "
                            f"- bar index out of range"
                        )
                    )
                    skipped_count += 1
                    continue

                # Calculate ATR at signal bar
                atr_val = self._calculate_atr(df, bar_index)

                # Calculate new stop loss and target
                stop_loss, target = _professional_sl_target(
                    df=df,
                    bar_index=bar_index,
                    center_price=float(record.center_price),
                    is_bullish=record.is_bullish,
                    atr_now=atr_val,
                    timeframe=record.timeframe,
                )

                # Display changes
                old_sl = float(record.outer_bottom if record.is_bullish else record.outer_top)
                old_target = float(record.outer_top if record.is_bullish else record.outer_bottom)
                
                self.stdout.write(
                    f"\n{idx}. {record.symbol} {record.timeframe} "
                    f"{'BUY' if record.is_bullish else 'SELL'} @ ${float(record.center_price):.2f}"
                )
                self.stdout.write(f"   Reversal Time: {record.reversal_time}")
                self.stdout.write(
                    f"   OLD: SL=${old_sl:.2f}, Target=${old_target:.2f}, "
                    f"Risk=${abs(float(record.center_price) - old_sl):.2f}"
                )
                self.stdout.write(
                    f"   NEW: SL=${stop_loss:.2f}, Target=${target:.2f}, "
                    f"Risk=${abs(float(record.center_price) - stop_loss):.2f}"
                )

                # Save to database (if not dry run)
                if not dry_run:
                    with transaction.atomic():
                        record.stop_loss = stop_loss
                        record.target = target
                        # Also update outer_top/outer_bottom for backward compatibility
                        if record.is_bullish:
                            record.outer_bottom = stop_loss
                            record.outer_top = target
                        else:
                            record.outer_top = stop_loss
                            record.outer_bottom = target
                        record.save()
                    self.stdout.write(self.style.SUCCESS("   ✅ Saved to database"))
                else:
                    self.stdout.write(self.style.WARNING("   🔍 Dry run - not saved"))

                success_count += 1

            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(
                        f"❌ Error processing {record.symbol} {record.timeframe} @ {record.reversal_time}: {e}"
                    )
                )
                logger.exception(f"Error recalculating signal {record.id}")

        # Summary
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 80))
        self.stdout.write(self.style.SUCCESS('SUMMARY'))
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(f"Total records: {total_count}")
        self.stdout.write(self.style.SUCCESS(f"✅ Successfully processed: {success_count}"))
        self.stdout.write(self.style.WARNING(f"⚠️  Skipped: {skipped_count}"))
        self.stdout.write(self.style.ERROR(f"❌ Errors: {error_count}"))
        
        if dry_run:
            self.stdout.write(self.style.WARNING("\n🔍 DRY RUN - No changes were saved"))
            self.stdout.write("Run without --dry-run to apply changes")
        else:
            self.stdout.write(self.style.SUCCESS("\n✅ Changes saved to database"))

    def _fetch_ohlcv_data(self, symbol, timeframe, reversal_time):
        """Fetch historical OHLCV data from Binance.US API"""
        try:
            # Convert timeframe to Binance format
            interval_map = {
                '1m': '1m', '3m': '3m', '5m': '5m', '15m': '15m',
                '30m': '30m', '1h': '1h', '2h': '2h', '4h': '4h',
                '6h': '6h', '8h': '8h', '12h': '12h', '1d': '1d',
                '3d': '3d', '1w': '1w', '1M': '1M',
            }
            interval = interval_map.get(timeframe, '15m')

            # Fetch data from 100 candles before reversal_time to 10 candles after
            start_time = int((reversal_time - timedelta(hours=100)).timestamp() * 1000)
            end_time = int((reversal_time + timedelta(hours=10)).timestamp() * 1000)

            url = 'https://api.binance.com/api/v3/klines'
            params = {
                'symbol': symbol,
                'interval': interval,
                'startTime': start_time,
                'endTime': end_time,
                'limit': 1000,
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if not data:
                return None

            # Convert to DataFrame
            df = pd.DataFrame(data, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                'taker_buy_quote', 'ignore'
            ])

            # Convert types
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df['open'] = df['open'].astype(float)
            df['high'] = df['high'].astype(float)
            df['low'] = df['low'].astype(float)
            df['close'] = df['close'].astype(float)
            df['volume'] = df['volume'].astype(float)

            return df

        except Exception as e:
            logger.error(f"Error fetching OHLCV data for {symbol} {timeframe}: {e}")
            return None

    def _find_bar_index(self, df, reversal_time):
        """Find the bar index closest to reversal_time"""
        try:
            import pytz
            
            # Ensure reversal_time is timezone-aware (UTC)
            if reversal_time.tzinfo is None:
                reversal_time = pytz.UTC.localize(reversal_time)
            
            # Ensure DataFrame timestamps are timezone-aware (UTC)
            if df['timestamp'].dt.tz is None:
                df['timestamp'] = df['timestamp'].dt.tz_localize('UTC')
            else:
                df['timestamp'] = df['timestamp'].dt.tz_convert('UTC')
            
            # Find the index of the candle closest to reversal_time
            df['time_diff'] = abs(df['timestamp'] - reversal_time)
            closest_idx = df['time_diff'].idxmin()
            return closest_idx
        except Exception as e:
            logger.error(f"Error finding bar index: {e}")
            return -1

    def _calculate_atr(self, df, bar_index, period=14):
        """Calculate ATR at the given bar index"""
        try:
            if bar_index < period:
                # Not enough data for ATR, use fallback
                return abs(float(df['close'].iloc[bar_index])) * 0.002

            # Calculate True Range
            high = df['high'].iloc[max(0, bar_index - period):bar_index + 1]
            low = df['low'].iloc[max(0, bar_index - period):bar_index + 1]
            close = df['close'].iloc[max(0, bar_index - period):bar_index + 1]
            prev_close = close.shift(1)

            tr1 = high - low
            tr2 = (high - prev_close).abs()
            tr3 = (low - prev_close).abs()
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

            # Calculate ATR (exponential moving average of TR)
            atr = tr.ewm(span=period, adjust=False).mean().iloc[-1]
            return float(atr)

        except Exception as e:
            logger.error(f"Error calculating ATR: {e}")
            # Fallback: 0.2% of price
            return abs(float(df['close'].iloc[bar_index])) * 0.002
