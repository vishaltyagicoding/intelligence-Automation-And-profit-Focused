"""
Payment Signals
===============
Auto-create subscription on user registration
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import Subscription

User = get_user_model()


@receiver(post_save, sender=User)
def create_user_subscription(sender, instance, created, **kwargs):
    """
    Automatically create subscription on user signup
    Respects trial_allowed field from device fingerprinting
    
    IMPORTANT: 
    - trial_status='active' for trial users (3-day access)
    - manual_subscription='deactivated' for trial users
    - manual_subscription='activated' ONLY for paid users (after payment)
    """
    if created:
        # Check if subscription already exists (created in verify_otp)
        if hasattr(instance, 'subscription'):
            return
        
        # Create subscription based on trial_allowed
        if instance.trial_allowed:
            # User gets 3-day free trial
            subscription = Subscription.objects.create(user=instance)
            subscription.activate_trial()
            
            # Set trial_status to 'active' and manual_subscription to 'deactivated'
            instance.trial_status = 'active'  # Trial is ACTIVE
            instance.manual_subscription = 'deactivated'  # NOT a paid user
            instance.save(update_fields=['trial_status', 'manual_subscription'])
            
            print(f"✅ Trial activated for new user: {instance.email} - trial_status='active', manual_subscription='deactivated'")
        else:
            # User does NOT get trial - create expired subscription
            subscription = Subscription.objects.create(
                user=instance,
                plan='trial',
                status='expired',
                trial_used=True,
                trial_start=timezone.now(),
                trial_end=timezone.now()
            )
            
            # Set both to inactive/deactivated
            instance.trial_status = 'inactive'
            instance.manual_subscription = 'deactivated'
            instance.save(update_fields=['trial_status', 'manual_subscription'])
            
            print(f"⚠️  No trial for new user: {instance.email} (device already used) - trial_status='inactive', manual_subscription='deactivated'")
