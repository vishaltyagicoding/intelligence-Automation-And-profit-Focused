"""
User Management Tasks
=====================
Celery tasks for user and subscription management
"""
import logging
from celery import shared_task
from django.utils import timezone
from django.contrib.auth import get_user_model
from payments.models import Subscription
from .email_utils import send_subscription_deactivated_email

User = get_user_model()
logger = logging.getLogger(__name__)


@shared_task
def check_and_expire_subscriptions():
    """
    Check for expired subscriptions (both trial and paid) and deactivate them
    Runs every 1 minute to ensure exact expiration time
    """
    try:
        now = timezone.now()
        expired_count = 0
        
        # Import email functions
        from users.email_utils import send_trial_expired_email, send_subscription_deactivated_email
        
        # 1. Find all TRIAL subscriptions that have expired (exact time check)
        expired_trials = Subscription.objects.filter(
            status='trial',
            trial_end__lte=now
        ).select_related('user')
        
        for subscription in expired_trials:
            user = subscription.user
            
            # Update subscription status
            subscription.status = 'expired'
            subscription.save(update_fields=['status'])
            
            # Update user trial_status to 'inactive' and keep manual_subscription as 'deactivated'
            user.trial_status = 'inactive'  # Trial is now INACTIVE
            user.manual_subscription = 'deactivated'  # Still not a paid user
            user.save(update_fields=['trial_status', 'manual_subscription'])
            
            # Send TRIAL expiration email (different from paid subscription)
            try:
                send_trial_expired_email(user.email, user.username or user.email)
                logger.info(f"✅ Trial expired for {user.email} at {now.strftime('%Y-%m-%d %H:%M:%S')} - trial_status set to 'inactive'")
            except Exception as e:
                logger.error(f"❌ Failed to send trial expiration email to {user.email}: {e}")
            
            expired_count += 1
        
        # 2. Find all PAID subscriptions that have expired (exact time check)
        expired_paid = Subscription.objects.filter(
            status='active',
            end_date__lte=now
        ).select_related('user')
        
        for subscription in expired_paid:
            user = subscription.user
            
            # Update subscription status
            subscription.status = 'expired'
            subscription.save(update_fields=['status'])
            
            # Update user manual_subscription to 'deactivated'
            if user.manual_subscription == 'activated':
                user.manual_subscription = 'deactivated'
                user.save(update_fields=['manual_subscription'])
                
                # Send PAID subscription expiration email (different from trial)
                try:
                    send_subscription_deactivated_email(user.email, user.username or user.email)
                    logger.info(f"✅ Paid subscription expired for {user.email} at {now.strftime('%Y-%m-%d %H:%M:%S')}")
                except Exception as e:
                    logger.error(f"❌ Failed to send deactivation email to {user.email}: {e}")
                
                expired_count += 1
        
        # Only log if subscriptions were expired (reduce log noise)
        if expired_count > 0:
            logger.info(f"✅ Expired {expired_count} subscription(s) at {now.strftime('%Y-%m-%d %H:%M:%S')}")
        
        return {
            'success': True,
            'expired_count': expired_count,
            'checked_at': now.isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to check expired subscriptions: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }
