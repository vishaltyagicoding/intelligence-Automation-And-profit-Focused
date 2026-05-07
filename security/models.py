"""
Security models for 2FA and audit.
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
import pyotp


class TwoFactorAuth(models.Model):
    """
    Two-factor authentication for users.
    """
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='two_factor')
    secret_key = models.CharField(max_length=32)
    is_enabled = models.BooleanField(default=False)
    backup_codes = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.username} - 2FA {'Enabled' if self.is_enabled else 'Disabled'}"
    
    def generate_secret(self):
        """Generate new TOTP secret."""
        self.secret_key = pyotp.random_base32()
        self.save()
        return self.secret_key
    
    def get_totp_uri(self):
        """Get TOTP URI for QR code."""
        return pyotp.totp.TOTP(self.secret_key).provisioning_uri(
            name=self.user.email,
            issuer_name='NeuralTrade'
        )
    
    def verify_token(self, token: str) -> bool:
        """Verify TOTP token."""
        totp = pyotp.TOTP(self.secret_key)
        is_valid = totp.verify(token, valid_window=1)
        
        if is_valid:
            self.last_used_at = timezone.now()
            self.save()
        
        return is_valid


class LoginAttempt(models.Model):
    """
    Track login attempts for security.
    """
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    username = models.CharField(max_length=150)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    success = models.BooleanField(default=False)
    failure_reason = models.CharField(max_length=200, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['username', 'timestamp']),
            models.Index(fields=['ip_address', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.username} - {'Success' if self.success else 'Failed'} - {self.timestamp}"


class APIKeyVault(models.Model):
    """
    Encrypted storage for API keys.
    """
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='api_keys')
    service_name = models.CharField(max_length=100)
    encrypted_api_key = models.TextField()
    encrypted_api_secret = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['user', 'service_name']
    
    def __str__(self):
        return f"{self.user.username} - {self.service_name}"
