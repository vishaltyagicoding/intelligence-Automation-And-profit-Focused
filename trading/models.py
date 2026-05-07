"""
Trading models for NeuralTrade platform.
"""

from django.conf import settings
from django.db import models
from django.utils import timezone


class Subscription(models.Model):
    """Subscription state for premium AI signal access."""

    TIER_MONTHLY = "MONTHLY"
    TIER_YEARLY = "YEARLY"
    TIER_CHOICES = [
        (TIER_MONTHLY, "Monthly"),
        (TIER_YEARLY, "Yearly"),
    ]

    STATUS_ACTIVE = "ACTIVE"
    STATUS_INACTIVE = "INACTIVE"
    STATUS_CANCELLED = "CANCELLED"
    STATUS_EXPIRED = "EXPIRED"
    STATUS_CHOICES = [
        (STATUS_ACTIVE, "Active"),
        (STATUS_INACTIVE, "Inactive"),
        (STATUS_CANCELLED, "Cancelled"),
        (STATUS_EXPIRED, "Expired"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="trading_subscription",  # Changed to avoid conflict with payments.Subscription
    )
    tier = models.CharField(max_length=20, choices=TIER_CHOICES, default=TIER_MONTHLY)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_INACTIVE)
    started_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    auto_renew = models.BooleanField(default=True)
    provider_customer_id = models.CharField(max_length=120, blank=True)
    provider_subscription_id = models.CharField(max_length=120, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["status", "expires_at"]),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.tier} - {self.status}"

    @property
    def is_active(self) -> bool:
        """Return True when subscription is valid and not expired."""
        if self.status != self.STATUS_ACTIVE:
            return False
        if self.expires_at and self.expires_at <= timezone.now():
            return False
        return True


class Trade(models.Model):
    """Model to store historical trade execution details."""

    TRADE_TYPE_CHOICES = [
        ("BUY", "Buy"),
        ("SELL", "Sell"),
    ]

    MARKET_CHOICES = [
        ("CRYPTO", "Cryptocurrency"),
        ("COMMODITY", "Commodity"),
    ]

    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("EXECUTED", "Executed"),
        ("CANCELLED", "Cancelled"),
        ("FAILED", "Failed"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="trades")
    symbol = models.CharField(max_length=20)
    market = models.CharField(max_length=10)
    trade_type = models.CharField(max_length=4, choices=TRADE_TYPE_CHOICES)
    quantity = models.DecimalField(max_digits=18, decimal_places=8)
    entry_price = models.DecimalField(max_digits=18, decimal_places=8)
    exit_price = models.DecimalField(max_digits=18, decimal_places=8, null=True, blank=True)
    stop_loss = models.DecimalField(max_digits=18, decimal_places=8)
    target = models.DecimalField(max_digits=18, decimal_places=8)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="PENDING")
    pnl = models.DecimalField(max_digits=18, decimal_places=8, null=True, blank=True)
    slippage = models.DecimalField(max_digits=10, decimal_places=6, default=0)
    order_id = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    executed_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["symbol", "market"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.trade_type} {self.symbol} - {self.status}"


class TradingSession(models.Model):
    """Model to track daily trading sessions."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="trading_sessions")  # Changed to avoid conflict with users.UserSession
    date = models.DateField(default=timezone.now)
    trades_count = models.IntegerField(default=0)
    total_pnl = models.DecimalField(max_digits=18, decimal_places=8, default=0)
    win_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ["user", "date"]
        ordering = ["-date"]

    def __str__(self):
        return f"{self.user.username} - {self.date}"


class MarketSignal(models.Model):
    """Model to store AI-generated visual signal events for the frontend."""

    ACTION_BUY = "BUY"
    ACTION_SELL = "SELL"
    ACTION_HOLD = "HOLD"
    ACTION_STOP_LOSS = "STOP_LOSS"
    SIGNAL_CHOICES = [
        (ACTION_BUY, "Buy"),
        (ACTION_SELL, "Sell"),
        (ACTION_HOLD, "Hold"),
        (ACTION_STOP_LOSS, "Stop Loss"),
    ]

    STATUS_OPEN = "OPEN"
    STATUS_CLOSED = "CLOSED"
    STATUS_STOPPED = "STOPPED"
    STATUS_CHOICES = [
        (STATUS_OPEN, "Open"),
        (STATUS_CLOSED, "Closed"),
        (STATUS_STOPPED, "Stopped"),
    ]

    symbol = models.CharField(max_length=20)
    market = models.CharField(max_length=10, default="CRYPTO")
    action = models.CharField(max_length=20, choices=SIGNAL_CHOICES, default=ACTION_HOLD)
    confidence = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    signal_price = models.DecimalField(max_digits=18, decimal_places=8, default=0)
    exit_price = models.DecimalField(max_digits=18, decimal_places=8, null=True, blank=True)
    stop_loss = models.DecimalField(max_digits=18, decimal_places=8, null=True, blank=True)
    target = models.DecimalField(max_digits=18, decimal_places=8, null=True, blank=True)
    profit = models.DecimalField(max_digits=18, decimal_places=8, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_OPEN)
    closed_at = models.DateTimeField(null=True, blank=True)
    message = models.TextField(default="")
    color = models.CharField(max_length=20, default="#fdd835")
    ai_context = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_broadcast = models.BooleanField(default=False)
    is_executed = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["symbol", "created_at"]),
            models.Index(fields=["action", "created_at"]),
            models.Index(fields=["status", "created_at"]),
        ]

    def __str__(self):
        return f"{self.action} {self.symbol} @ {self.signal_price}"

    def websocket_payload(self) -> dict:
        """Return frontend-ready websocket payload."""
        signal_price = float(self.exit_price) if self.action == self.ACTION_STOP_LOSS and self.exit_price else float(self.signal_price)
        return {
            "asset": self.symbol,
            "timestamp": int(self.created_at.timestamp()),
            "price": signal_price,
            "action": self.action,
            "message": self.message,
            "color": self.color,
        }

    def calculate_profit(self):
        """Calculate profit/loss based on entry and exit prices."""
        if self.exit_price and self.signal_price:
            if self.action == self.ACTION_BUY:
                self.profit = float(self.exit_price) - float(self.signal_price)
            elif self.action == self.ACTION_SELL:
                self.profit = float(self.signal_price) - float(self.exit_price)
            self.save(update_fields=['profit'])




class ReversalZoneData(models.Model):
    """
    Store calculated reversal entry zones data
    Updated every 4 hours by Celery task
    """
    symbol = models.CharField(max_length=20, db_index=True)
    timeframe = models.CharField(max_length=10, default='4h')
    
    # Reversal zones data (JSON)
    zones = models.JSONField(default=list, help_text="List of reversal zones with coordinates")
    path_segments = models.JSONField(default=list, help_text="Synthetic path connecting reversals")
    status = models.JSONField(default=dict, help_text="Status panel data")
    config = models.JSONField(default=dict, help_text="Configuration used for calculation")
    
    # Metadata
    last_updated = models.DateTimeField(auto_now=True)
    candle_count = models.IntegerField(default=0)
    current_price = models.DecimalField(max_digits=20, decimal_places=8, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'reversal_zone_data'
        unique_together = ['symbol', 'timeframe']
        ordering = ['-last_updated']
        indexes = [
            models.Index(fields=['symbol', 'timeframe']),
            models.Index(fields=['-last_updated']),
        ]
    
    def __str__(self):
        return f"{self.symbol} {self.timeframe} - {len(self.zones)} zones"
    
    def to_api_response(self) -> dict:
        """Format for API response"""
        return {
            'symbol': self.symbol,
            'timeframe': self.timeframe,
            'zones': self.zones,
            'path_segments': self.path_segments,
            'status': self.status,
            'config': self.config,
            'last_updated': self.last_updated.isoformat(),
            'candle_count': self.candle_count,
            'current_price': float(self.current_price) if self.current_price else None,
        }
