"""
Shoonya/Finvasia API client wrapper.
"""

import logging
from NorenRestApiPy.NorenApi import NorenApi
from django.conf import settings

logger = logging.getLogger(__name__)


class ShoonyaClientWrapper:
    """
    Wrapper for Shoonya API client.
    """
    
    def __init__(self):
        self.api = NorenApi(
            host='https://api.shoonya.com/NorenWClientTP/',
            websocket='wss://api.shoonya.com/NorenWSTP/'
        )
    
    def get_quotes(self, exchange, token):
        """Get market quotes."""
        try:
            quotes = self.api.get_quotes(
                exchange=exchange,
                token=token
            )
            return quotes
        except Exception as e:
            logger.error(f"Shoonya quotes error: {e}")
            return None
    
    def place_order(self, buy_or_sell, product_type, exchange, tradingsymbol, 
                    quantity, price_type, price=0.0):
        """Place an order."""
        try:
            order = self.api.place_order(
                buy_or_sell=buy_or_sell,
                product_type=product_type,
                exchange=exchange,
                tradingsymbol=tradingsymbol,
                quantity=quantity,
                discloseqty=0,
                price_type=price_type,
                price=price,
                trigger_price=None,
                retention='DAY',
                remarks='NeuralTrade'
            )
            return order
        except Exception as e:
            logger.error(f"Order placement error: {e}")
            return None
