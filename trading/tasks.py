"""
Celery tasks for automated trading operations.
Includes auto-login, token refresh, and market monitoring.
"""

import logging
import pyotp
import redis
from celery import shared_task
from django.conf import settings
from django.utils import timezone
from binance.client import Client as BinanceClient
from NorenRestApiPy.NorenApi import NorenApi

logger = logging.getLogger(__name__)

# Initialize Redis client
redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    decode_responses=True
)


@shared_task(bind=True, max_retries=3)
def auto_login_shoonya(self):
    """
    Automated login for Shoonya/Finvasia using TOTP.
    Scheduled daily at 8:45 AM via Celery Beat.
    """
    try:
        logger.info("Starting Shoonya auto-login...")
        
        # Initialize Shoonya API
        api = NorenApi(
            host='https://api.shoonya.com/NorenWClientTP/',
            websocket='wss://api.shoonya.com/NorenWSTP/'
        )
        
        # Generate TOTP
        totp = pyotp.TOTP(settings.SHOONYA_TOTP_SECRET)
        totp_code = totp.now()
        
        # Perform login
        response = api.login(
            userid=settings.SHOONYA_USER_ID,
            password=settings.SHOONYA_PASSWORD,
            twoFA=totp_code,
            vendor_code=settings.SHOONYA_VENDOR_CODE,
            api_secret=settings.SHOONYA_API_KEY,
            imei=settings.SHOONYA_IMEI
        )
        
        if response and response.get('stat') == 'Ok':
            # Store token in Redis with 24-hour expiry
            token = response.get('susertoken')
            redis_client.setex(
                settings.REDIS_KEY_SHOONYA_TOKEN,
                86400,  # 24 hours
                token
            )
            
            logger.info("Shoonya auto-login successful")
            return {'status': 'success', 'token': token}
        else:
            error_msg = response.get('emsg', 'Unknown error')
            logger.error(f"Shoonya login failed: {error_msg}")
            raise Exception(error_msg)
            
    except Exception as e:
        logger.error(f"Shoonya auto-login error: {e}")
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))


@shared_task(bind=True, max_retries=3)
def refresh_binance_token(self):
    """
    Refresh Binance.US API session token.
    Scheduled every 6 hours via Celery Beat.
    """
    try:
        logger.info("Refreshing Binance.US token...")
        
        # Initialize Binance.US client
        client = BinanceClient(
            api_key=settings.BINANCE_API_KEY,
            api_secret=settings.BINANCE_API_SECRET,
            tld='us'  # Use Binance.US
        )
        
        # Test connection and get server time
        server_time = client.get_server_time()
        
        # Store session info in Redis
        session_data = {
            'api_key': settings.BINANCE_API_KEY,
            'server_time': server_time['serverTime'],
            'refreshed_at': timezone.now().isoformat()
        }
        
        redis_client.setex(
            settings.REDIS_KEY_BINANCE_TOKEN,
            21600,  # 6 hours
            str(session_data)
        )
        
        logger.info("Binance token refresh successful")
        return {'status': 'success', 'server_time': server_time}
        
    except Exception as e:
        logger.error(f"Binance token refresh error: {e}")
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))


@shared_task
def market_watch_heartbeat():
    """
    Market watch heartbeat task.
    Runs every 1 second to monitor active trades and market conditions.
    """
    try:
        # Get active trades from Redis
        active_trades = redis_client.smembers(settings.REDIS_KEY_ACTIVE_TRADES)
        
        # Update heartbeat timestamp
        redis_client.set('market:heartbeat', timezone.now().isoformat())
        
        # Monitor each active trade
        for trade_id in active_trades:
            monitor_trade.delay(trade_id)
        
        return {'status': 'success', 'active_trades': len(active_trades)}
        
    except Exception as e:
        logger.error(f"Market watch heartbeat error: {e}")
        return {'status': 'error', 'message': str(e)}


@shared_task
def monitor_trade(trade_id):
    """
    Monitor individual trade for stop-loss and target conditions.
    """
    try:
        # Get trade data from Redis
        trade_key = f"trade:{trade_id}"
        trade_data = redis_client.hgetall(trade_key)
        
        if not trade_data:
            return {'status': 'not_found'}
        
        # Get current market price
        symbol = trade_data.get('symbol')
        current_price = get_current_price(symbol)
        
        # Check stop-loss and target
        entry_price = float(trade_data.get('entry_price', 0))
        stop_loss = float(trade_data.get('stop_loss', 0))
        target = float(trade_data.get('target', 0))
        
        if current_price <= stop_loss or current_price >= target:
            # Trigger exit
            execute_exit.delay(trade_id, current_price)
        
        return {'status': 'monitored', 'trade_id': trade_id}
        
    except Exception as e:
        logger.error(f"Trade monitoring error: {e}")
        return {'status': 'error', 'message': str(e)}


@shared_task
def execute_exit(trade_id, exit_price):
    """
    Execute trade exit.
    """
    try:
        logger.info(f"Executing exit for trade {trade_id} at {exit_price}")
        
        # Implementation for order execution
        # This will be expanded in Phase 2
        
        # Remove from active trades
        redis_client.srem(settings.REDIS_KEY_ACTIVE_TRADES, trade_id)
        
        return {'status': 'success', 'trade_id': trade_id}
        
    except Exception as e:
        logger.error(f"Exit execution error: {e}")
        return {'status': 'error', 'message': str(e)}


@shared_task
def cleanup_expired_tokens():
    """
    Cleanup expired tokens and stale data from Redis.
    Runs daily at midnight.
    """
    try:
        logger.info("Cleaning up expired tokens...")
        
        # Redis automatically handles expiry, but we can do additional cleanup
        # Remove old market data
        pattern = "market:ticks:*"
        for key in redis_client.scan_iter(match=pattern):
            # Keep only last 24 hours of data
            redis_client.ltrim(key, 0, 86400)
        
        logger.info("Cleanup completed")
        return {'status': 'success'}
        
    except Exception as e:
        logger.error(f"Cleanup error: {e}")
        return {'status': 'error', 'message': str(e)}


def get_current_price(symbol):
    """
    Helper function to get current market price from Redis.
    """
    try:
        redis_key = f"market:ticks:{symbol}"
        latest_tick = redis_client.lindex(redis_key, 0)
        
        if latest_tick:
            import json
            tick_data = json.loads(latest_tick)
            return float(tick_data.get('price', 0))
        
        return 0.0
    except Exception as e:
        logger.error(f"Error getting current price: {e}")
        return 0.0



@shared_task(bind=True, max_retries=2)
def calculate_reversal_zones(self, symbol: str = 'BTCUSD'):
    """
    Calculate reversal entry zones for a given symbol
    Runs every 4 hours via Celery Beat
    
    Args:
        symbol: Trading pair (e.g., 'BTCUSD', 'ETHUSD', 'SOLUSD')
    """
    try:
        import ccxt
        import pandas as pd
        from .reversal_engine import ReversalEngine
        from .models import ReversalZoneData
        
        logger.info(f"🔍 Calculating reversal zones for {symbol}...")
        
        # Initialize exchange
        exchange = ccxt.binance({
            'enableRateLimit': True,
            'options': {'defaultType': 'spot'}
        })
        
        # Convert symbol format (BTCUSD -> BTC/USDT)
        binance_symbol = symbol.replace('USD', '/USDT')
        
        # Fetch 4-hour candles (500 bars for sufficient history)
        timeframe = '4h'
        limit = 500
        
        logger.info(f"📊 Fetching {limit} {timeframe} candles for {binance_symbol}...")
        ohlcv = exchange.fetch_ohlcv(binance_symbol, timeframe, limit=limit)
        
        # Convert to DataFrame
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        logger.info(f"✅ Fetched {len(df)} candles from {df['timestamp'].iloc[0]} to {df['timestamp'].iloc[-1]}")
        
        # Initialize reversal engine with default config
        config = {
            'confirm_bars': 0,
            'preset': 'Low',  # "Low" or "Very Low"
            'calc_mode': 'Average',  # "Average" or "High/Low"
            'avg_len': 5,
            'atr_len': 5,
            'custom_abs': 0.05,
            'max_zones': 8,
            'zone_extend': 10,
            'zone_thickness_pct': 0.03,
            'level_extend': 10,
            'max_levels': 12,
            'show_synthetic_path': True,
            'max_synthetic_lines': 40,
        }
        
        engine = ReversalEngine(config)
        
        # Calculate reversals
        logger.info(f"🤖 Running reversal detection algorithm...")
        result = engine.process_candles(df)
        
        logger.info(f"✅ Found {len(result['zones'])} reversal zones")
        logger.info(f"✅ Generated {len(result['path_segments'])} path segments")
        logger.info(f"📊 Status: {result['status']['last_signal']} | Tracking: {result['status']['tracking']}")
        
        # Store in database
        zone_data, created = ReversalZoneData.objects.update_or_create(
            symbol=symbol,
            timeframe=timeframe,
            defaults={
                'zones': result['zones'],
                'path_segments': result['path_segments'],
                'status': result['status'],
                'config': result['config'],
                'last_updated': timezone.now(),
                'candle_count': len(df),
                'current_price': float(df['close'].iloc[-1]),
            }
        )
        
        action = "Created" if created else "Updated"
        logger.info(f"✅ {action} reversal zone data for {symbol}")
        
        # Cache in Redis for fast API access
        cache_key = f"reversal_zones:{symbol}:{timeframe}"
        redis_client.setex(
            cache_key,
            3600 * 4,  # 4 hours TTL
            str(result)
        )
        
        logger.info(f"✅ Cached reversal data in Redis: {cache_key}")
        
        return {
            'symbol': symbol,
            'zones_count': len(result['zones']),
            'status': result['status']['last_signal'],
            'success': True
        }
        
    except Exception as exc:
        logger.error(f"❌ Error calculating reversal zones for {symbol}: {exc}", exc_info=True)
        raise self.retry(exc=exc, countdown=300)  # Retry after 5 minutes


@shared_task
def calculate_all_reversal_zones():
    """
    Calculate reversal zones for all supported symbols
    Runs every 4 hours
    """
    symbols = ['BTCUSD', 'ETHUSD', 'SOLUSD', 'XAUUSD', 'LTCUSD']
    
    logger.info(f"🚀 Starting reversal zone calculation for {len(symbols)} symbols...")
    
    results = []
    for symbol in symbols:
        try:
            result = calculate_reversal_zones.delay(symbol)
            results.append({'symbol': symbol, 'task_id': result.id})
            logger.info(f"✅ Queued reversal calculation for {symbol}: {result.id}")
        except Exception as e:
            logger.error(f"❌ Failed to queue {symbol}: {e}")
            results.append({'symbol': symbol, 'error': str(e)})
    
    return {
        'total_symbols': len(symbols),
        'queued': len([r for r in results if 'task_id' in r]),
        'failed': len([r for r in results if 'error' in r]),
        'results': results
    }