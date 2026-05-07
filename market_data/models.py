"""
Market data models.
"""

from django.db import models


class OHLCV(models.Model):
    """OHLCV candlestick data model."""
    
    symbol = models.CharField(max_length=20)
    market = models.CharField(max_length=10)
    timestamp = models.DateTimeField()
    open = models.DecimalField(max_digits=18, decimal_places=8)
    high = models.DecimalField(max_digits=18, decimal_places=8)
    low = models.DecimalField(max_digits=18, decimal_places=8)
    close = models.DecimalField(max_digits=18, decimal_places=8)
    volume = models.DecimalField(max_digits=18, decimal_places=8)
    
    class Meta:
        unique_together = ['symbol', 'timestamp']
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['symbol', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.symbol} - {self.timestamp}"
