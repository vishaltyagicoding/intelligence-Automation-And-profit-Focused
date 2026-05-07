"""
Kill Switch - Emergency system shutdown for trading.
Monitors API latency and broker connections.
"""

import logging
import time
import redis
from typing import Dict, List
from django.conf import settings
from django.utils import timezone
from decimal import Decimal

logger = logging.getLogger(__name__)


class KillSwitch:
    """
    Emergency kill switch for trading operations.
    Monitors system health and closes positions if needed.
    """
    
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )
        
        self.latency_threshold = 500  # milliseconds
        self.is_active = False
        self.trigger_reason = None
        
        logger.info("Kill Switch initialized")
    
    def check_api_latency(self, api_name: str) -> float:
        """
        Check API latency.
        Returns latency in milliseconds.
        """
        try:
            start_time = time.time()
            
            # Ping API (simplified)
            if api_name == 'binance':
                from market_data.binance_client import BinanceClientWrapper
                client = BinanceClientWrapper()
                client.get_ticker_price('BTCUSDT')
            elif api_name == 'shoonya':
                # Ping Shoonya API
                pass
            
            latency = (time.time() - start_time) * 1000
            
            # Store in Redis
            self.redis_client.setex(
                f"api:latency:{api_name}",
                60,
                str(latency)
            )
            
            return latency
            
        except Exception as e:
            logger.error(f"Error checking {api_name} latency: {e}")
            return 9999  # High value to trigger kill switch
    
    def check_broker_connection(self, broker: str) -> bool:
        """
        Check if broker connection is alive.
        """
        try:
            if broker == 'binance':
                from market_data.binance_client import BinanceClientWrapper
                client = BinanceClientWrapper()
                result = client.get_ticker_price('BTCUSDT')
                return result is not None
            
            elif broker == 'shoonya':
                # Check Shoonya connection
                token = self.redis_client.get(settings.REDIS_KEY_SHOONYA_TOKEN)
                return token is not None
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking {broker} connection: {e}")
            return False
    
    def should_trigger(self) -> tuple[bool, str]:
        """
        Check if kill switch should be triggered.
        Returns (should_trigger, reason)
        """
        # Check API latencies
        binance_latency = self.check_api_latency('binance')
        if binance_latency > self.latency_threshold:
            return True, f"Binance API latency too high: {binance_latency:.2f}ms"
        
        # Check broker connections
        if not self.check_broker_connection('binance'):
            return True, "Binance connection lost"
        
        if not self.check_broker_connection('shoonya'):
            return True, "Shoonya connection lost"
        
        # Check Redis connection
        try:
            self.redis_client.ping()
        except:
            return True, "Redis connection lost"
        
        return False, ""
    
    def activate(self, reason: str):
        """
        Activate kill switch - stop all trading.
        """
        if self.is_active:
            logger.warning("Kill switch already active")
            return
        
        logger.critical(f"KILL SWITCH ACTIVATED: {reason}")
        
        self.is_active = True
        self.trigger_reason = reason
        
        # Set flag in Redis
        self.redis_client.set('system:kill_switch:active', '1')
        self.redis_client.set('system:kill_switch:reason', reason)
        self.redis_client.set('system:kill_switch:timestamp', timezone.now().isoformat())
        
        # Close all open positions
        self.close_all_positions()
        
        # Stop new entries
        self.stop_new_entries()
        
        # Send alerts
        self.send_alerts(reason)
    
    def deactivate(self):
        """
        Deactivate kill switch - resume trading.
        """
        logger.info("Kill switch deactivated")
        
        self.is_active = False
        self.trigger_reason = None
        
        # Clear Redis flags
        self.redis_client.delete('system:kill_switch:active')
        self.redis_client.delete('system:kill_switch:reason')
        self.redis_client.delete('system:kill_switch:timestamp')
    
    def close_all_positions(self):
        """
        Emergency close all open positions.
        """
        try:
            from trading.models import Trade
            
            # Get all open trades
            open_trades = Trade.objects.filter(
                status='EXECUTED',
                closed_at__isnull=True
            )
            
            logger.warning(f"Closing {open_trades.count()} open positions")
            
            for trade in open_trades:
                try:
                    # Close position with market order
                    self._close_position(trade)
                except Exception as e:
                    logger.error(f"Error closing trade {trade.id}: {e}")
            
        except Exception as e:
            logger.error(f"Error closing all positions: {e}")
    
    def _close_position(self, trade):
        """
        Close individual position.
        """
        try:
            if trade.market == 'CRYPTO':
                from market_data.binance_client import BinanceClientWrapper
                client = BinanceClientWrapper()
                
                # Place opposite order
                side = 'SELL' if trade.trade_type == 'BUY' else 'BUY'
                client.place_order(
                    symbol=trade.symbol,
                    side=side,
                    order_type='MARKET',
                    quantity=float(trade.quantity)
                )
            
            elif trade.market == 'COMMODITY':
                from market_data.shoonya_client import ShoonyaClientWrapper
                client = ShoonyaClientWrapper()
                
                # Place opposite order
                side = 'S' if trade.trade_type == 'BUY' else 'B'
                client.place_order(
                    buy_or_sell=side,
                    product_type='I',
                    exchange='MCX',
                    tradingsymbol=trade.symbol,
                    quantity=int(trade.quantity),
                    price_type='MKT',
                    price=0.0
                )
            
            # Update trade status
            trade.status = 'CANCELLED'
            trade.closed_at = timezone.now()
            trade.save()
            
            logger.info(f"Position closed: {trade.id}")
            
        except Exception as e:
            logger.error(f"Error closing position {trade.id}: {e}")
    
    def stop_new_entries(self):
        """
        Stop new trade entries.
        """
        # Set flag to prevent new trades
        self.redis_client.set('system:trading:disabled', '1')
        logger.warning("New trade entries stopped")
    
    def send_alerts(self, reason: str):
        """
        Send alerts to admins.
        """
        try:
            from django.core.mail import mail_admins
            
            subject = "KILL SWITCH ACTIVATED - NeuralTrade"
            message = f"""
            The kill switch has been activated.
            
            Reason: {reason}
            Timestamp: {timezone.now().isoformat()}
            
            All open positions have been closed.
            New trade entries have been stopped.
            
            Please investigate immediately.
            """
            
            mail_admins(subject, message, fail_silently=True)
            
            logger.info("Kill switch alerts sent")
            
        except Exception as e:
            logger.error(f"Error sending alerts: {e}")
    
    def is_trading_allowed(self) -> bool:
        """
        Check if trading is currently allowed.
        """
        if self.is_active:
            return False
        
        # Check Redis flag
        disabled = self.redis_client.get('system:trading:disabled')
        if disabled == '1':
            return False
        
        return True


# Global kill switch instance
kill_switch = KillSwitch()
