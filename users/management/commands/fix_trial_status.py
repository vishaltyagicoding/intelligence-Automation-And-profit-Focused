"""
Fix Trial Status for Existing Users
====================================
Sets trial_status='active' for users currently on trial
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from payments.models import Subscription

User = get_user_model()


class Command(BaseCommand):
    help = 'Fix trial_status for existing users'

    def handle(self, *args, **options):
        self.stdout.write("=" * 70)
        self.stdout.write(self.style.SUCCESS("Fixing Trial Status for Existing Users"))
        self.stdout.write("=" * 70)
        
        fixed_count = 0
        
        # Find all users with active trials
        active_trials = Subscription.objects.filter(
            status='trial',
            trial_end__gt=timezone.now()
        ).select_related('user')
        
        self.stdout.write(f"\nFound {active_trials.count()} users with active trials")
        
        for subscription in active_trials:
            user = subscription.user
            
            # Set trial_status to 'active'
            user.trial_status = 'active'
            user.manual_subscription = 'deactivated'
            user.save(update_fields=['trial_status', 'manual_subscription'])
            
            self.stdout.write(f"✅ Fixed {user.email}: trial_status='active', manual_subscription='deactivated'")
            fixed_count += 1
        
        # Find all users with expired trials
        expired_trials = Subscription.objects.filter(
            status='expired',
            trial_end__lte=timezone.now()
        ).select_related('user')
        
        self.stdout.write(f"\nFound {expired_trials.count()} users with expired trials")
        
        for subscription in expired_trials:
            user = subscription.user
            
            # Set trial_status to 'inactive'
            user.trial_status = 'inactive'
            user.manual_subscription = 'deactivated'
            user.save(update_fields=['trial_status', 'manual_subscription'])
            
            self.stdout.write(f"⚠️  Fixed {user.email}: trial_status='inactive', manual_subscription='deactivated'")
            fixed_count += 1
        
        # Find all users with paid subscriptions
        paid_subs = Subscription.objects.filter(
            status='active'
        ).select_related('user')
        
        self.stdout.write(f"\nFound {paid_subs.count()} users with paid subscriptions")
        
        for subscription in paid_subs:
            user = subscription.user
            
            # Set trial_status to 'inactive' and manual_subscription to 'activated'
            user.trial_status = 'inactive'
            user.manual_subscription = 'activated'
            user.save(update_fields=['trial_status', 'manual_subscription'])
            
            self.stdout.write(f"👑 Fixed {user.email}: trial_status='inactive', manual_subscription='activated'")
            fixed_count += 1
        
        self.stdout.write("\n" + "=" * 70)
        self.stdout.write(self.style.SUCCESS(f"✅ Fixed {fixed_count} users"))
        self.stdout.write("=" * 70)
