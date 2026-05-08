"""
Binance API client wrapper.
"""

import logging
from binance.client import Client
from binance.exceptions import BinanceAPIException
from django.conf import settings

logger = logging.getLogger(__name__)


class BinanceClientWrapper:
    """
    Wrapper for Binance.US API client with error handling.
    """
    
    def __init__(self):
        self.client = Client(
            api_key=settings.BINANCE_API_KEY,
            api_secret=settings.BINANCE_API_SECRET,
            tld='us'  # Use Binance.US
        )
    
    def get_ticker_price(self, symbol):
        """Get current ticker price."""
        try:
            ticker = self.client.get_symbol_ticker(symbol=symbol)
            return float(ticker['price'])
        except BinanceAPIException as e:
            logger.error(f"Binance API error: {e}")
            return None
    
    def get_klines(self, symbol, interval='1m', limit=100):
        """Get historical klines/candlestick data."""
        try:
            klines = self.client.get_klines(
                symbol=symbol,
                interval=interval,
                limit=limit
            )
            return klines
        except BinanceAPIException as e:
            logger.error(f"Binance API error: {e}")
            return []
    
    def place_order(self, symbol, side, order_type, quantity, price=None):
        """Place an order."""
        try:
            order_params = {
                'symbol': symbol,
                'side': side,
                'type': order_type,
                'quantity': quantity,
            }
            
            if order_type == 'LIMIT':
                order_params['price'] = price
                order_params['timeInForce'] = 'GTC'
            
            order = self.client.create_order(**order_params)
            return order
        except BinanceAPIException as e:
            logger.error(f"Order placement error: {e}")
            return None
