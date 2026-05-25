from django.db import models
from django.utils import timezone


class ReversalZone(models.Model):
    symbol = models.CharField(max_length=20)
    timeframe = models.CharField(max_length=10, default='4h')  # ADDED MISSING FIELD
    reversal_time = models.DateTimeField()
    center_price = models.DecimalField(max_digits=20, decimal_places=8)
    stop_loss = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)  # NEW: Universal stop loss
    target = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)     # NEW: Universal target
    outer_top = models.DecimalField(max_digits=20, decimal_places=8)
    outer_bottom = models.DecimalField(max_digits=20, decimal_places=8)
    core_top = models.DecimalField(max_digits=20, decimal_places=8)
    core_bottom = models.DecimalField(max_digits=20, decimal_places=8)
    is_bullish = models.BooleanField(default=True)
    label_text = models.CharField(max_length=10, default='BUY')
    bar_index = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Status tracking fields for history page
    status = models.CharField(max_length=20, default='OPEN', choices=[
        ('OPEN', 'Open'),
        ('TARGET_HIT', 'Target Hit'),
        ('SL_HIT', 'Stop Loss Hit'),
    ])
    status_updated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'reversal_zones'
        ordering = ['-reversal_time']
        indexes = [
            models.Index(fields=['symbol', 'timeframe', '-reversal_time']),
            models.Index(fields=['symbol', 'is_bullish']),
        ]
        unique_together = [['symbol', 'timeframe', 'reversal_time']]

    def __str__(self):
        return f"{self.symbol} {self.timeframe} {'BUY' if self.is_bullish else 'SELL'} @ {self.center_price}"


class SyntheticPathSegment(models.Model):
    symbol = models.CharField(max_length=20)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    start_price = models.DecimalField(max_digits=20, decimal_places=8)
    end_price = models.DecimalField(max_digits=20, decimal_places=8)
    start_bar = models.IntegerField(default=0)
    end_bar = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['start_time']

    def __str__(self):
        return f"{self.symbol} path {self.start_time} -> {self.end_time}"


class ReversalStatus(models.Model):
    symbol = models.CharField(max_length=20, unique=True)
    last_signal = models.CharField(max_length=10, default='NONE')
    tracking = models.CharField(max_length=10, default='NONE')
    current_price = models.DecimalField(max_digits=20, decimal_places=8, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Reversal Statuses'

    def __str__(self):
        return f"{self.symbol} - {self.last_signal}"
