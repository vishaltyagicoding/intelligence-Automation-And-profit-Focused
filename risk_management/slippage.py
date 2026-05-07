"""
Slippage control and smart order execution logic.
"""

import logging
from decimal import Decimal
from django.conf import settings

logger = logging.getLogger(__name__)


class SlippageController:
    """
    Manages slippage control and smart order execution.
    """
    
    def __init__(self, market='CRYPTO'):
        self.market = market
        self.threshold = self._get_threshold()
    
    def _get_threshold(self):
        """Get slippage threshold based on market."""
        if self.market == 'CRYPTO':
            return Decimal(str(settings.SLIPPAGE_THRESHOLD_CRYPTO))
        else:
            return Decimal(str(settings.SLIPPAGE_THRESHOLD_COMMODITY))
    
    def calculate_slippage(self, signal_price, execution_price):
        """
        Calculate slippage percentage.
        """
        signal_price = Decimal(str(signal_price))
        execution_price = Decimal(str(execution_price))
        
        if signal_price == 0:
            return Decimal('0')
        
        slippage = abs(execution_price - signal_price) / signal_price
        return slippage
    
    def is_acceptable(self, signal_price, execution_price):
        """
        Check if slippage is within acceptable threshold.
        """
        slippage = self.calculate_slippage(signal_price, execution_price)
        return slippage <= self.threshold
    
    def get_order_type(self, signal_price, current_price):
        """
        Determine order type based on slippage.
        Returns: 'MARKET', 'LIMIT', or 'CANCEL'
        """
        if self.is_acceptable(signal_price, current_price):
            return 'MARKET'
        
        slippage = self.calculate_slippage(signal_price, current_price)
        
        if slippage <= self.threshold * Decimal('2'):
            # Use limit order if slippage is moderate
            return 'LIMIT'
        else:
            # Cancel if slippage is too high
            return 'CANCEL'
    
    def calculate_market_impact(self, quantity, order_book_depth):
        """
        Calculate market impact cost.
        """
        # Simplified implementation
        # In production, analyze order book depth
        impact = Decimal(str(quantity)) / Decimal(str(order_book_depth))
        return min(impact, Decimal('0.01'))  # Cap at 1%
