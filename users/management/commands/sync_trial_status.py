"""
Sync Trial Status Command
==========================
Fixes data inconsistency between User.trial_status and Subscription.status
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from payments.models import Subscription

User = get_user_model()


class Command(BaseCommand):
    help = 'Synchronize trial_status field with subscription status'

    def handle(self, *args, **options):
        self.stdout.write("=" * 80)
        self.stdout.write(self.style.SUCCESS("🔄 Synchronizing Trial Status"))
        self.stdout.write("=" * 80)
        
        fixed_count = 0
        
        # Find users with trial_status='active' but expired subscription
        users = User.objects.filter(trial_status='active').select_related('subscription')
        
        for user in users:
            try:
                subscription = user.subscription
                
                # Check if subscription is expired
                if subscription.status == 'expired':
                    self.stdout.write(f"\n❌ Inconsistency found: {user.email}")
                    self.stdout.write(f"   User.trial_status: {user.trial_status}")
                    self.stdout.write(f"   Subscription.status: {subscription.status}")
                    self.stdout.write(f"   Subscription.trial_end: {subscription.trial_end}")
                    
                    # Fix: Set trial_status to 'inactive'
                    user.trial_status = 'inactive'
                    user.save(update_fields=['trial_status'])
                    
                    self.stdout.write(self.style.SUCCESS(f"   ✅ Fixed: Set trial_status='inactive'"))
                    fixed_count += 1
                
                # Check if trial has expired but status not updated
                elif subscription.status == 'trial' and subscription.trial_end:
                    if timezone.now() > subscription.trial_end:
                        self.stdout.write(f"\n❌ Expired trial not updated: {user.email}")
                        self.stdout.write(f"   Trial ended: {subscription.trial_end}")
                        self.stdout.write(f"   Current time: {timezone.now()}")
                        
                        # Fix: Update both subscription and user
                        subscription.status = 'expired'
                        subscription.save(update_fields=['status'])
                        
                        user.trial_status = 'inactive'
                        user.save(update_fields=['trial_status'])
                        
                        self.stdout.write(self.style.SUCCESS(f"   ✅ Fixed: Set subscription.status='expired' and trial_status='inactive'"))
                        fixed_count += 1
                
            except Subscription.DoesNotExist:
                self.stdout.write(f"\n⚠️  User {user.email} has no subscription")
        
        # Check paid users
        paid_users = User.objects.filter(manual_subscription='activated').select_related('subscription')
        
        for user in paid_users:
            try:
                subscription = user.subscription
                
                # Paid users should have trial_status='inactive'
                if user.trial_status == 'active':
                    self.stdout.write(f"\n❌ Paid user with active trial: {user.email}")
                    self.stdout.write(f"   User.trial_status: {user.trial_status}")
                    self.stdout.write(f"   User.manual_subscription: {user.manual_subscription}")
                    
                    # Fix: Set trial_status to 'inactive'
                    user.trial_status = 'inactive'
                    user.save(update_fields=['trial_status'])
                    
                    self.stdout.write(self.style.SUCCESS(f"   ✅ Fixed: Set trial_status='inactive' for paid user"))
                    fixed_count += 1
                
            except Subscription.DoesNotExist:
                self.stdout.write(f"\n⚠️  Paid user {user.email} has no subscription")
        
        self.stdout.write("\n" + "=" * 80)
        if fixed_count > 0:
            self.stdout.write(self.style.SUCCESS(f"✅ Fixed {fixed_count} user(s)"))
        else:
            self.stdout.write(self.style.SUCCESS("✅ All users are in sync!"))
        self.stdout.write("=" * 80)
