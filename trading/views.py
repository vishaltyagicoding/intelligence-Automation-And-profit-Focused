"""
API views for trading operations.
"""

import logging
import requests as http_requests
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.utils import timezone
import datetime
import redis
from django.conf import settings

from .models import Trade, MarketSignal
from .serializers import TradeSerializer, MarketSignalSerializer

logger = logging.getLogger(__name__)

redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    decode_responses=True
)


class TradeViewSet(viewsets.ModelViewSet):
    """ViewSet for managing trades."""
    
    serializer_class = TradeSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Trade.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class MarketSignalViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing market signals and history."""
    
    serializer_class = MarketSignalSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return all signals, optionally filtered by symbol or action."""
        queryset = MarketSignal.objects.all()
        
        symbol = self.request.query_params.get('symbol', None)
        if symbol:
            queryset = queryset.filter(symbol=symbol.upper())
        
        action = self.request.query_params.get('action', None)
        if action:
            queryset = queryset.filter(action=action.upper())
        
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter.upper())
        
        return queryset.order_by('-created_at')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def system_status(request):
    """Get system status and health check."""
    
    try:
        redis_status = redis_client.ping()
        shoonya_token = redis_client.exists(settings.REDIS_KEY_SHOONYA_TOKEN)
        binance_token = redis_client.exists(settings.REDIS_KEY_BINANCE_TOKEN)
        active_trades = redis_client.scard(settings.REDIS_KEY_ACTIVE_TRADES)
        heartbeat = redis_client.get('market:heartbeat')
        
        return Response({
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'redis': 'connected' if redis_status else 'disconnected',
            'auth': {
                'shoonya': 'active' if shoonya_token else 'inactive',
                'binance': 'active' if binance_token else 'inactive',
            },
            'trading': {
                'active_trades': active_trades,
                'last_heartbeat': heartbeat,
            }
        })
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


@api_view(['GET'])
@permission_classes([AllowAny])
def list_reversal_symbols(request):
    """
    List all symbols with available reversal zone data

    GET /api/trading/reversal-zones/
    """
    try:
        from .models import ReversalZoneData
        
        zones = ReversalZoneData.objects.all().order_by('-last_updated')
        
        data = [{
            'symbol': z.symbol,
            'timeframe': z.timeframe,
            'zones_count': len(z.zones),
            'last_updated': z.last_updated.isoformat(),
            'current_price': float(z.current_price) if z.current_price else None,
            'last_signal': z.status.get('last_signal', 'Unknown'),
        } for z in zones]
        
        return Response({
            'symbols': data,
            'total': len(data)
        })
    
    except Exception as e:
        logger.error(f"❌ Error listing reversal symbols: {e}", exc_info=True)
        return Response({'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_reversal_zones(request, symbol):
    """
    Get reversal zones for a specific symbol and timeframe.
    Returns:
      - Live zones from calculator (current market data)
      - Historical zones from DB (permanently stored signals)
      Both merged and deduplicated by bar_index.

    GET /api/trading/reversal-zones/BTCUSD/?timeframe=1m
    """
    import pandas as pd
    from reversal_zones.reversal_calculator import ReversalZoneCalculator
    from reversal_zones.models import ReversalZone
    from django.core.cache import cache
    from django.utils.dateparse import parse_datetime

    timeframe = request.GET.get('timeframe', '4h')

    TF_MAP = {
        '1m': '1m', '3m': '3m', '5m': '5m', '10m': '5m',
        '15m': '15m', '30m': '30m', '1h': '1h', '2h': '2h',
        '4h': '4h', '1d': '1d',
    }
    binance_tf = TF_MAP.get(timeframe, '4h')

    # Special mapping: XAUUSD uses PAXG (Paxos Gold) on Binance
    # XAUUSD maps to PAXGUSDT (Paxos Gold) — real gold-backed token on Binance
    ASSET_BINANCE_MAP = {'XAUUSD': 'PAXGUSDT'}
    sym_upper = symbol.upper()
    if sym_upper in ASSET_BINANCE_MAP:
        binance_symbol = ASSET_BINANCE_MAP[sym_upper]
    elif sym_upper.endswith('USD') and not sym_upper.endswith('USDT'):
        binance_symbol = sym_upper[:-3] + 'USDT'
    else:
        binance_symbol = sym_upper

    cache_key = f"reversal_zones_v4:{binance_symbol}:{timeframe}"
    cached = cache.get(cache_key)
    if cached:
        return Response(cached)

    try:
        # Binance.com (global) — same data source as TradingView
        # This ensures signals match TradingView exactly
        limit = 500 if timeframe == '1d' else 1000
        url = (
            f"https://api.binance.com/api/v3/klines"
            f"?symbol={binance_symbol}&interval={binance_tf}&limit={limit}"
        )
        resp = http_requests.get(url, timeout=15)
        resp.raise_for_status()
        klines = resp.json()

        if not klines:
            return Response({'success': False, 'error': 'No data from Binance'}, status=500)

        df = pd.DataFrame(klines, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_volume', 'trades',
            'taker_buy_base', 'taker_buy_quote', 'ignore'
        ])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
        df['open']  = df['open'].astype(float)
        df['high']  = df['high'].astype(float)
        df['low']   = df['low'].astype(float)
        df['close'] = df['close'].astype(float)
        df.set_index('timestamp', inplace=True)

        if timeframe == '10m':
            rows = []
            times = []
            for i in range(0, len(df) - 1, 2):
                a, b = df.iloc[i], df.iloc[i + 1]
                rows.append({
                    'open': float(a['open']), 'high': max(float(a['high']), float(b['high'])),
                    'low':  min(float(a['low']),  float(b['low'])),  'close': float(b['close']),
                })
                times.append(df.index[i])
            df = pd.DataFrame(rows, index=times)

        # ── Step 2: Run calculator ONLY to get current status + detect the
        # single most-recent signal (the one not yet saved to DB).
        # We do NOT use the calculator's full zone list for display — those
        # zones repaint every time the window shifts. Only the DB records
        # (written once and never changed) are used for historical display.
        calculator = ReversalZoneCalculator(
            preset="Low",
            calc_mode="Average",
            avg_len=5,
            atr_len=5,
            custom_abs=0.05,
            confirm_bars=0,  # Pine Script default: 0 (no extra delay) — matches TradingView exactly,
            timeframe=timeframe
        )
        result = calculator.process_ohlcv_data(df)
        live_zones = result['zones']

        # ── Step 3: Build the all_zones list exclusively from the DB ──────────
        # DB signals are written ONCE (by the Celery task) and never updated,
        # so their timestamps are permanently locked to the exact candle where
        # the signal was first detected. This eliminates repainting entirely.
        import datetime as _dt
        from django.utils import timezone as _tz

        since = _tz.now() - _dt.timedelta(days=150)
        db_records = ReversalZone.objects.filter(
            symbol=binance_symbol,
            timeframe=timeframe,
            reversal_time__gte=since,
        ).order_by('reversal_time')

        all_zones = []
        db_timestamps = set()

        for rec in db_records:
            ts = rec.reversal_time
            ts_iso = ts.isoformat() if hasattr(ts, 'isoformat') else str(ts)
            db_timestamps.add(ts_iso)

            is_bull = rec.is_bullish
            entry   = float(rec.center_price)
            if rec.stop_loss and rec.target:
                outer_top_val = float(rec.target    if is_bull else rec.stop_loss)
                outer_bot_val = float(rec.stop_loss if is_bull else rec.target)
            else:
                outer_top_val = float(rec.outer_top)
                outer_bot_val = float(rec.outer_bottom)

            all_zones.append({
                'bar_index':    rec.bar_index,
                'center_price': entry,
                'outer_top':    outer_top_val,
                'outer_bottom': outer_bot_val,
                'core_top':     float(rec.core_top),
                'core_bottom':  float(rec.core_bottom),
                'is_bullish':   is_bull,
                'label':        rec.label_text,
                'timestamp':    ts_iso,
                'source':       'db',
            })

        # ── Step 4: Append the most-recent live signal ONLY if it is genuinely
        # new (not yet saved to DB) AND alternates correctly with the last DB signal.
        #
        # ANTI-CONSECUTIVE BUG FIX:
        # Without the alternation check here, the live_pending zone could be the
        # SAME type as the last DB signal (e.g. DB last = BUY, live_pending = BUY).
        # This would render consecutive BUY→BUY on the chart even though the DB
        # alternation is correct. The live calculator sometimes fires the same type
        # again on the very latest candle before the Celery task has saved a
        # balancing SELL in between.
        if live_zones:
            newest_live = live_zones[-1]
            nl_ts = newest_live.get('timestamp') or newest_live.get('reversal_time')
            nl_ts_iso = nl_ts.isoformat() if hasattr(nl_ts, 'isoformat') else str(nl_ts)
            nl_is_bull = newest_live['is_bullish']
            nl_label   = 'BUY' if nl_is_bull else 'SELL'

            # Get last DB signal type for alternation check
            last_db_label = all_zones[-1]['label'] if all_zones else None

            # Accept live_pending ONLY if:
            # 1. Its timestamp is not already in DB (genuinely new candle)
            # 2. It ALTERNATES with the last DB signal (BUY after SELL, SELL after BUY)
            ts_is_new      = nl_ts_iso not in db_timestamps
            type_alternates = (last_db_label is None) or (last_db_label != nl_label)

            if ts_is_new and type_alternates:
                nl_ts_iso_z = nl_ts_iso if ('+' in nl_ts_iso or nl_ts_iso.endswith('Z')) else nl_ts_iso + '+00:00'
                all_zones.append({
                    'bar_index':    newest_live['bar_index'],
                    'center_price': float(newest_live['center_price']),
                    'outer_top':    float(newest_live['outer_top']),
                    'outer_bottom': float(newest_live['outer_bottom']),
                    'core_top':     float(newest_live['core_top']),
                    'core_bottom':  float(newest_live['core_bottom']),
                    'is_bullish':   nl_is_bull,
                    'label':        nl_label,
                    'timestamp':    nl_ts_iso_z,
                    'source':       'live_pending',
                })

        path_data = []
        for seg in result.get('path_segments', []):
            path_data.append({
                'start_bar':   seg['start_bar'],
                'end_bar':     seg['end_bar'],
                'start_price': float(seg['start_price']),
                'end_price':   float(seg['end_price']),
                'start_time':  seg['start_time'].isoformat(),
                'end_time':    seg['end_time'].isoformat(),
            })

        data = {
            'symbol':        binance_symbol,
            'timeframe':     timeframe,
            'zones':         all_zones,
            'path_segments': path_data,
            'status':        result['status'],
            'config':        {'level_extend': 10},
            'live_count':    len(all_zones),
        }

        # Cache for only 30 seconds so the live_pending signal stays fresh,
        # but DB signals are stable enough to serve from cache.
        cache.set(cache_key, {'success': True, 'data': data}, timeout=30)
        return Response({'success': True, 'data': data})

    except http_requests.exceptions.Timeout:
        logger.error(f"❌ Binance API timeout for {binance_symbol} {timeframe}")
        return Response({'success': False, 'error': 'Binance API timeout'}, status=500)

    except http_requests.exceptions.RequestException as e:
        logger.error(f"❌ Binance API error: {e}")
        return Response({'success': False, 'error': f'Binance API error: {str(e)}'}, status=500)

    except Exception as e:
        logger.error(f"❌ Error in get_reversal_zones [{binance_symbol} {timeframe}]: {e}", exc_info=True)
        return Response({'success': False, 'error': str(e)}, status=500)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_signal_history(request, symbol):
    """
    Return ALL permanently stored BUY/SELL signals from DB for a symbol+timeframe.
    NO filtering - returns exactly what the calculator generated.
    This ensures signals match TradingView exactly.

    GET /api/trading/signal-history/BTCUSD/?timeframe=1m
    """
    from reversal_zones.models import ReversalZone
    from django.utils import timezone as tz

    timeframe = request.GET.get('timeframe', '4h')

    # Special mapping: XAUUSD uses PAXG (Paxos Gold) on Binance
    ASSET_BINANCE_MAP = {'XAUUSD': 'PAXGUSDT'}
    sym_upper = symbol.upper()
    if sym_upper in ASSET_BINANCE_MAP:
        db_symbol = ASSET_BINANCE_MAP[sym_upper]
    elif sym_upper.endswith('USD') and not sym_upper.endswith('USDT'):
        db_symbol = sym_upper[:-3] + 'USDT'
    else:
        db_symbol = sym_upper

    try:
        # Fetch all records from last 5 months (matches history page window)
        since = tz.now() - datetime.timedelta(days=150)
        records = ReversalZone.objects.filter(
            symbol=db_symbol,
            timeframe=timeframe,
            reversal_time__gte=since,
        ).order_by('reversal_time')

        # NO FILTERING - return all signals exactly as calculator generated them
        # The calculator already enforces alternation via swing_dir logic
        # Any additional filtering would cause mismatch with TradingView
        signals = []
        for rec in records:
            is_bull   = rec.is_bullish
            entry     = round(float(rec.center_price), 2)
            outer_top = round(float(rec.outer_top),    2)
            outer_bot = round(float(rec.outer_bottom), 2)
            core_top  = round(float(rec.core_top),     2)
            core_bot  = round(float(rec.core_bottom),  2)

            # NEW: Use the dedicated stop_loss and target fields if available
            # This ensures history API shows the universal calculation values
            if rec.stop_loss and rec.target:
                stop_loss = round(float(rec.stop_loss), 2)
                target    = round(float(rec.target), 2)
            else:
                # Fallback to outer_top/outer_bottom for old records
                if is_bull:
                    stop_loss = outer_bot
                    target    = outer_top
                else:
                    stop_loss = outer_top
                    target    = outer_bot

            signals.append({
                'bar_index':    rec.bar_index,
                'is_bullish':   is_bull,
                'center_price': entry,
                'stop_loss':    stop_loss,
                'target':       target,
                'outer_top':    outer_top,
                'outer_bottom': outer_bot,
                'core_top':     core_top,
                'core_bottom':  core_bot,
                'label':        rec.label_text,
                'timestamp':    rec.reversal_time.isoformat(),
                'status':       rec.status,  # NEW: Include status for history page
            })

        return Response({
            'success':   True,
            'symbol':    db_symbol,
            'timeframe': timeframe,
            'count':     len(signals),
            'signals':   signals,
        })

    except Exception as e:
        logger.error(f"Error fetching signal history: {e}", exc_info=True)
        return Response({'success': False, 'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([AllowAny])
def trigger_history_calculation(request, symbol):
    """
    Trigger 30-day historical signal calculation for a symbol.
    POST /api/trading/calculate-history/BTCUSD/
    POST /api/trading/calculate-history/all/
    """
    from reversal_zones.tasks import (
        calculate_history_for_symbol_timeframe,
        calculate_all_history,
    )

    if symbol.lower() == 'all':
        calculate_all_history.apply_async()
        return Response({'success': True, 'message': 'Queued full history calculation for all symbols'})

    timeframes = request.data.get('timeframes', ["1m","3m","5m","10m","15m","30m","1h","2h","4h","1d"])
    sym_upper  = symbol.upper()

    for tf in timeframes:
        calculate_history_for_symbol_timeframe.apply_async(args=[sym_upper, tf])

    return Response({
        'success':    True,
        'symbol':     sym_upper,
        'timeframes': timeframes,
        'message':    f'Queued history calculation for {sym_upper} × {len(timeframes)} timeframes',
    })