from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class SignalAlert(models.Model):
    """
    Model to store user signal alert preferences
    """
    CRYPTO_CHOICES = [
        ('BTCUSD', 'Bitcoin'),
        ('ETHUSD', 'Ethereum'),
        ('LTCUSD', 'Litecoin'),
        ('XAUUSD', 'Gold'),
    ]
    
    TIMEFRAME_CHOICES = [
        ('5m', '5 Minutes'),
        ('15m', '15 Minutes'),
        ('30m', '30 Minutes'),
        ('1h', '1 Hour'),
        ('2h', '2 Hours'),
        ('4h', '4 Hours'),
        ('1d', '1 Day'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='signal_alerts')
    crypto = models.CharField(max_length=10, choices=CRYPTO_CHOICES)
    timeframe = models.CharField(max_length=5, choices=TIMEFRAME_CHOICES)
    email = models.EmailField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'signal_alerts'
        unique_together = ['user', 'crypto', 'timeframe']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.crypto} {self.timeframe}"