"""
Risk Manager Agent for trade validation and risk control.
"""

import logging
from decimal import Decimal
from django.conf import settings
from .slippage import SlippageController

logger = logging.getLogger(__name__)


class RiskManager:
    """
    Manages risk assessment and trade validation.
    """
    
    def __init__(self, user):
        self.user = user
        self.max_trades_per_day = settings.MAX_TRADES_PER_DAY
    
    def validate_trade(self, trade_data):
        """
        Validate trade before execution.
        """
        validations = {
            'daily_limit': self._check_daily_limit(),
            'balance': self._check_balance(trade_data),
            'position_size': self._check_position_size(trade_data),
            'slippage': self._check_slippage(trade_data),
        }
        
        is_valid = all(validations.values())
        
        return {
            'valid': is_valid,
            'checks': validations,
            'message': self._get_validation_message(validations)
        }
    
    def _check_daily_limit(self):
        """Check if daily trade limit is reached."""
        from trading.models import Trade
        from django.utils import timezone
        
        today = timezone.now().date()
        trades_today = Trade.objects.filter(
            user=self.user,
            created_at__date=today
        ).count()
        
        return trades_today < self.max_trades_per_day
    
    def _check_balance(self, trade_data):
        """Check if user has sufficient balance."""
        required = Decimal(str(trade_data['quantity'])) * Decimal(str(trade_data['entry_price']))
        return self.user.profile.balance >= required
    
    def _check_position_size(self, trade_data):
        """Check if position size is within limits."""
        position_value = Decimal(str(trade_data['quantity'])) * Decimal(str(trade_data['entry_price']))
        max_position = self.user.profile.balance * Decimal('0.1')  # 10% max
        return position_value <= max_position
    
    def _check_slippage(self, trade_data):
        """Check slippage tolerance."""
        controller = SlippageController(market=trade_data.get('market', 'CRYPTO'))
        return controller.is_acceptable(
            trade_data['signal_price'],
            trade_data['entry_price']
        )
    
    def _get_validation_message(self, validations):
        """Generate validation message."""
        if all(validations.values()):
            return "Trade validated successfully"
        
        failed = [k for k, v in validations.items() if not v]
        return f"Validation failed: {', '.join(failed)}"
