"""
Custom User Model
=================
Extended user model with additional fields for NeuralTrade
"""
from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid


class User(AbstractUser):
    """
    Custom User Model
    Extends Django's AbstractUser with additional fields
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, db_index=True)
    
    # Profile fields
    phone = models.CharField(max_length=15, null=True, blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    bio = models.TextField(max_length=500, null=True, blank=True)
    
    # Account status
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=False)
    phone_verified = models.BooleanField(default=False)
    
    # Device Fingerprinting & Trial Management
    device_id = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    registration_ip = models.GenericIPAddressField(null=True, blank=True)
    registration_user_agent = models.TextField(null=True, blank=True)
    trial_used = models.BooleanField(default=False)  # Has this user used their free trial?
    trial_allowed = models.BooleanField(default=True)  # Is this user allowed a trial?
    
    # Trial Status (NEW FIELD)
    trial_status = models.CharField(
        max_length=20,
        choices=[('active', 'Active'), ('inactive', 'Inactive')],
        default='inactive',
        verbose_name='Trial Status',
        help_text='Trial status - Active during 3-day trial, Inactive after trial ends or when paid subscription is activated'
    )
    
    # Manual Subscription Control (for admin)
    manual_subscription = models.CharField(
        max_length=20,
        choices=[('activated', 'Activated'), ('deactivated', 'Deactivated')],
        default='deactivated',  # Default is deactivated (only activated for PAID users)
        verbose_name='Subscription',
        help_text='Subscription status - Deactivated for trial users, Activated only for PAID users after payment confirmation'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)

    # Timezone preference — set automatically from browser on every login.
    # Used to format timestamps in email notifications to the user's local time.
    timezone = models.CharField(
        max_length=100,
        default='UTC',
        blank=True,
        help_text='IANA timezone name (e.g. Asia/Kolkata). Set automatically from browser.'
    )
    
    # Use email as username
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    class Meta:
        db_table = 'users'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['username']),
            models.Index(fields=['is_active']),
            models.Index(fields=['device_id']),  # Index for fast device lookup
            models.Index(fields=['registration_ip']),  # Index for IP-based checks
        ]
    
    def __str__(self):
        return self.email
    
    def get_full_name(self):
        """Return full name or email"""
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name if full_name else self.email
    
    def get_short_name(self):
        """Return first name or username"""
        return self.first_name or self.username
    
    def save(self, *args, **kwargs):
        """Override save to handle subscription changes"""
        # Skip email sending if update_fields is specified (bulk updates)
        skip_email = 'update_fields' in kwargs and kwargs['update_fields'] is not None
        
        # Save the user first to ensure the change is persisted
        is_new = self.pk is None
        old_manual_subscription = None
        
        # Check if this is an update (not a new user)
        if not is_new:
            try:
                old_instance = User.objects.get(pk=self.pk)
                old_manual_subscription = old_instance.manual_subscription
            except User.DoesNotExist:
                pass
        
        # Call parent save first
        super().save(*args, **kwargs)
        
        # Now handle subscription changes AFTER user is saved
        if not is_new and old_manual_subscription is not None and old_manual_subscription != self.manual_subscription:
            # Import here to avoid circular imports
            from datetime import timedelta
            from django.utils import timezone
            from payments.models import Subscription
            from users.email_utils import send_subscription_activated_email, send_subscription_deactivated_email
            
            if self.manual_subscription == 'activated':
                # Activate PAID subscription
                subscription, created = Subscription.objects.get_or_create(user=self)
                subscription.status = 'active'
                subscription.plan = 'monthly'
                subscription.start_date = timezone.now()
                subscription.end_date = timezone.now() + timedelta(days=30)
                subscription.save()
                
                # Set trial_status to 'inactive' when paid subscription is activated
                if self.trial_status == 'active':
                    self.trial_status = 'inactive'
                    User.objects.filter(pk=self.pk).update(trial_status='inactive')
                
                # Send activation email (only if not bulk update) with dates
                if not skip_email:
                    try:
                        send_subscription_activated_email(
                            self.email, 
                            self.username or self.email,
                            activation_date=subscription.start_date,
                            expiry_date=subscription.end_date
                        )
                    except:
                        pass
            
            elif self.manual_subscription == 'deactivated':
                # Deactivate subscription
                try:
                    subscription = Subscription.objects.get(user=self)
                    subscription.status = 'expired'
                    subscription.end_date = timezone.now()
                    subscription.save()
                except Subscription.DoesNotExist:
                    pass
                
                # Send deactivation email (only if not bulk update)
                if not skip_email:
                    try:
                        send_subscription_deactivated_email(self.email, self.username or self.email)
                    except:
                        pass


class UserSession(models.Model):
    """
    Track user sessions for security
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    token = models.TextField(db_index=True)  # Changed from CharField(max_length=255) to TextField for JWT tokens
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    last_activity = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_sessions'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.ip_address}"


class EmailVerification(models.Model):
    """
    Store OTP for email verification during registration
    User is NOT created until email is verified
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(db_index=True)
    username = models.CharField(max_length=150)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    password_hash = models.CharField(max_length=255)  # Store hashed password temporarily
    
    # Device fingerprinting
    device_id = models.CharField(max_length=255, null=True, blank=True)
    
    otp = models.CharField(max_length=6)
    is_verified = models.BooleanField(default=False)
    attempts = models.IntegerField(default=0)  # Track failed attempts
    
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()  # OTP expires after 10 minutes
    verified_at = models.DateTimeField(null=True, blank=True)
    
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        db_table = 'email_verifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email', 'is_verified']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"{self.email} - {'Verified' if self.is_verified else 'Pending'}"
    
    def is_expired(self):
        """Check if OTP has expired"""
        from django.utils import timezone
        return timezone.now() > self.expires_at
    
    def can_retry(self):
        """Check if user can retry (max 5 attempts)"""
        return self.attempts < 5


class PasswordReset(models.Model):
    """
    Store OTP for password reset
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_resets')
    email = models.EmailField(db_index=True)
    
    otp = models.CharField(max_length=6)
    is_used = models.BooleanField(default=False)
    attempts = models.IntegerField(default=0)  # Track failed attempts
    
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()  # OTP expires after 10 minutes
    used_at = models.DateTimeField(null=True, blank=True)
    
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        db_table = 'password_resets'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email', 'is_used']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"{self.email} - {'Used' if self.is_used else 'Pending'}"
    
    def is_expired(self):
        """Check if OTP has expired"""
        from django.utils import timezone
        return timezone.now() > self.expires_at
    
    def can_retry(self):
        """Check if user can retry (max 5 attempts)"""
        return self.attempts < 5


class DeviceFingerprint(models.Model):
    """
    Track device fingerprints for trial abuse prevention
    Stores all registration attempts from a device
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    device_id = models.CharField(max_length=255, db_index=True)  # FingerprintJS visitorId
    
    # User who registered with this device
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='device_fingerprints', null=True, blank=True)
    
    # Device information
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    
    # Trial tracking
    trial_granted = models.BooleanField(default=False)  # Was trial granted for this device?
    trial_count = models.IntegerField(default=0)  # How many times trial was attempted from this device
    
    # Timestamps
    first_seen = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)
    
    # Fraud detection
    is_blocked = models.BooleanField(default=False)  # Block suspicious devices
    block_reason = models.TextField(null=True, blank=True)
    
    class Meta:
        db_table = 'device_fingerprints'
        ordering = ['-last_seen']
        indexes = [
            models.Index(fields=['device_id']),
            models.Index(fields=['ip_address']),
            models.Index(fields=['trial_granted']),
            models.Index(fields=['is_blocked']),
        ]
        # Ensure device_id is unique per user (but same device can have multiple users)
    
    def __str__(self):
        return f"Device {self.device_id[:8]}... - Trial: {self.trial_granted}"
    
    def increment_trial_count(self):
        """Increment trial attempt counter"""
        self.trial_count += 1
        self.save(update_fields=['trial_count', 'last_seen'])
