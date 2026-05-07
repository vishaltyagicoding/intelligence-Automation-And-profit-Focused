"""
Serializers for trading models.
"""

from rest_framework import serializers
from .models import Trade, TradingSession, MarketSignal


class TradeSerializer(serializers.ModelSerializer):
    """Serializer for Trade model."""
    
    class Meta:
        model = Trade
        fields = [
            'id', 'symbol', 'market', 'trade_type', 'quantity',
            'entry_price', 'exit_price', 'stop_loss', 'target',
            'status', 'pnl', 'slippage', 'order_id',
            'created_at', 'executed_at', 'closed_at'
        ]
        read_only_fields = ['id', 'created_at', 'executed_at', 'closed_at', 'pnl']


class TradingSessionSerializer(serializers.ModelSerializer):
    """Serializer for TradingSession model."""
    
    class Meta:
        model = TradingSession
        fields = ['id', 'date', 'trades_count', 'total_pnl', 'win_rate', 'is_active']
        read_only_fields = ['id', 'date']


class MarketSignalSerializer(serializers.ModelSerializer):
    """Serializer for MarketSignal model."""
    
    timestamp = serializers.SerializerMethodField()
    entryPrice = serializers.DecimalField(source='signal_price', max_digits=18, decimal_places=8)
    exitPrice = serializers.DecimalField(source='exit_price', max_digits=18, decimal_places=8, allow_null=True)
    stopLoss = serializers.DecimalField(source='stop_loss', max_digits=18, decimal_places=8, allow_null=True)
    
    class Meta:
        model = MarketSignal
        fields = [
            'id', 'timestamp', 'symbol', 'market', 'action', 'confidence',
            'entryPrice', 'exitPrice', 'stopLoss', 'target', 'profit', 'status',
            'message', 'color', 'created_at', 'closed_at', 'is_executed'
        ]
        read_only_fields = ['id', 'created_at', 'closed_at', 'profit']
    
    def get_timestamp(self, obj):
        """Return ISO format timestamp."""
        return obj.created_at.isoformat()
