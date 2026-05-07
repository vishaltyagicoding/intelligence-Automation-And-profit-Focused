from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal
import uuid

User = get_user_model()


class PaymentInfo(models.Model):
    """
    Payment Information Model - NEW
    Stores payment details for subscription activations
    Only accessible by superuser alberttyagi123@gmail.com
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='payment_info_records',
        help_text='User associated with this payment'
    )
    user_name = models.CharField(
        max_length=255,
        help_text='Username from User table'
    )
    subscription_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text='Subscription price (numeric only)'
    )
    payment_valid_image = models.ImageField(
        upload_to='payment_proofs/%Y/%m/%d/',
        help_text='Payment proof image'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_payment_infos',
        help_text='Superuser who created this record'
    )
    
    class Meta:
        db_table = 'payment_info'
        verbose_name = 'Payment Info'
        verbose_name_plural = 'Payment Info'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user_name} - ${self.subscription_price}"
    
    def save(self, *args, **kwargs):
        # Ensure user_name matches the user's username
        if self.user:
            self.user_name = self.user.username
        super().save(*args, **kwargs)


# ============================================================================
# EXISTING MODELS - DO NOT MODIFY
# ============================================================================

class Payment(models.Model):
    """Payment Model - Existing"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    PAYMENT_TYPE_CHOICES = [
        ('subscription', 'Subscription'),
        ('renewal', 'Auto Renewal'),
        ('upgrade', 'Plan Upgrade'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    subscription = models.ForeignKey('Subscription', on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='INR')
    razorpay_order_id = models.CharField(max_length=100, unique=True)
    razorpay_payment_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    razorpay_signature = models.CharField(max_length=255, null=True, blank=True)
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES, default='subscription')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=50, null=True, blank=True)
    notes = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'payments'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['razorpay_order_id']),
            models.Index(fields=['razorpay_payment_id']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.amount} {self.currency} - {self.status}"
    
    def mark_success(self, razorpay_payment_id, razorpay_signature, payment_method=None):
        self.status = 'success'
        self.razorpay_payment_id = razorpay_payment_id
        self.razorpay_signature = razorpay_signature
        self.payment_method = payment_method
        self.paid_at = timezone.now()
        self.save()
    
    def mark_failed(self, error_message):
        self.status = 'failed'
        self.error_message = error_message
        self.save()


class Subscription(models.Model):
    """Subscription Model - Existing"""
    PLAN_CHOICES = [
        ('trial', '3-Day Free Trial'),
        ('monthly', 'Monthly Plan'),
        ('yearly', 'Yearly Plan'),
    ]
    
    STATUS_CHOICES = [
        ('trial', 'Trial Active'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='subscription')
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default='trial')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='trial')
    trial_start = models.DateTimeField(null=True, blank=True)
    trial_end = models.DateTimeField(null=True, blank=True)
    trial_used = models.BooleanField(default=False)
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    auto_renew = models.BooleanField(default=True)
    razorpay_subscription_id = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'subscriptions'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.plan} - {self.status}"
    
    def is_active(self):
        if self.status == 'trial' and self.trial_end:
            return timezone.now() < self.trial_end
        elif self.status == 'active' and self.end_date:
            return timezone.now() < self.end_date
        return False
    
    def days_remaining(self):
        if self.status == 'trial' and self.trial_end:
            delta = self.trial_end - timezone.now()
            return max(0, delta.days)
        elif self.status == 'active' and self.end_date:
            delta = self.end_date - timezone.now()
            return max(0, delta.days)
        return 0
    
    def activate_trial(self):
        from datetime import timedelta
        self.status = 'trial'
        self.plan = 'trial'
        self.trial_start = timezone.now()
        self.trial_end = timezone.now() + timedelta(days=3)
        self.trial_used = True
        self.save()
    
    def upgrade_to_paid(self, plan='monthly'):
        from datetime import timedelta
        self.plan = plan
        self.status = 'active'
        self.start_date = timezone.now()
        if plan == 'monthly':
            self.end_date = timezone.now() + timedelta(days=30)
        elif plan == 'yearly':
            self.end_date = timezone.now() + timedelta(days=365)
        self.save()


class WebhookLog(models.Model):
    """Webhook Log Model - Existing"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_type = models.CharField(max_length=100)
    payload = models.JSONField()
    processed = models.BooleanField(default=False)
    error = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'webhook_logs'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.event_type} - {self.created_at}"
