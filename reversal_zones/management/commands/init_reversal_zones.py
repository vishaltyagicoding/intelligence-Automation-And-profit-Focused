"""
Management command to initialize reversal zones for all symbols + timeframes.
Called from start_server.sh on startup.
"""

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Initialize reversal zones for all symbols and timeframes'

    def add_arguments(self, parser):
        parser.add_argument('--symbol', type=str, default=None,
                            help='Specific symbol e.g. BTCUSDT')
        parser.add_argument('--timeframe', type=str, default=None,
                            help='Specific timeframe e.g. 4h')
        parser.add_argument('--recent-only', action='store_true',
                            help='Only fetch recent signals (faster)')

    def handle(self, *args, **options):
        from reversal_zones.tasks import (
            calculate_all_history,
            calculate_history_for_symbol_timeframe,
            update_recent_signals_for_symbol_timeframe,
            update_all_recent_signals,
            SYMBOLS,
            ALL_TIMEFRAMES,
        )

        symbol    = options.get('symbol')
        timeframe = options.get('timeframe')
        recent    = options.get('recent_only', False)

        if symbol and timeframe:
            self.stdout.write(f'Calculating {symbol} {timeframe}...')
            if recent:
                update_recent_signals_for_symbol_timeframe.apply_async(
                    args=[symbol, timeframe]
                )
            else:
                calculate_history_for_symbol_timeframe.apply_async(
                    args=[symbol, timeframe]
                )
            self.stdout.write(self.style.SUCCESS(f'✅ Task queued: {symbol} {timeframe}'))

        else:
            # Full calculation for all symbols × timeframes
            self.stdout.write(
                f'Queuing full history for {len(SYMBOLS)} symbols × '
                f'{len(ALL_TIMEFRAMES)} timeframes...'
            )
            if recent:
                result = update_all_recent_signals.apply_async()
            else:
                result = calculate_all_history.apply_async()

            self.stdout.write(self.style.SUCCESS(
                f'✅ Queued full history calculation (task id: {result.id})'
            ))