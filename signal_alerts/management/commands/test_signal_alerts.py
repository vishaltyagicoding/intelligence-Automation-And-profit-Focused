"""
Management command to test signal alert email notifications
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from signal_alerts.models import SignalAlert
from signal_alerts.email_utils import send_signal_alert_email, notify_signal_subscribers

User = get_user_model()


class Command(BaseCommand):
    help = 'Test signal alert email notifications'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Email address to send test notification to',
        )
        parser.add_argument(
            '--username',
            type=str,
            help='Username for the test email',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n🔔 Testing Signal Alert System\n'))
        
        # Test 1: Send a test email
        if options.get('email') and options.get('username'):
            self.stdout.write('📧 Sending test email...')
            
            test_signal_data = {
                'crypto': 'BTCUSD',
                'timeframe': '1h',
                'signal_type': 'BUY',
                'entry_price': 45250.50,
                'stop_loss': 44800.00,
                'target': 46500.00,
                'timestamp': timezone.now().strftime('%Y-%m-%d %H:%M:%S UTC'),
            }
            
            success = send_signal_alert_email(
                email=options['email'],
                username=options['username'],
                signal_data=test_signal_data
            )
            
            if success:
                self.stdout.write(self.style.SUCCESS(f'✅ Test email sent to {options["email"]}'))
            else:
                self.stdout.write(self.style.ERROR(f'❌ Failed to send test email'))
        
        # Test 2: Check existing alerts
        self.stdout.write('\n📊 Checking existing signal alerts...')
        
        alerts = SignalAlert.objects.filter(is_active=True).select_related('user')
        
        if not alerts.exists():
            self.stdout.write(self.style.WARNING('⚠️  No active signal alerts found'))
            self.stdout.write('   Create alerts through the Signal Alerts page')
        else:
            self.stdout.write(self.style.SUCCESS(f'✅ Found {alerts.count()} active alert(s):'))
            for alert in alerts:
                self.stdout.write(
                    f'   • {alert.user.username} - {alert.crypto} {alert.timeframe} → {alert.email}'
                )
        
        # Test 3: Check paid subscribers
        self.stdout.write('\n👑 Checking paid subscribers...')
        
        # Try different field names based on the model structure
        try:
            paid_users = User.objects.filter(
                manual_subscription='activated'
            )
        except Exception:
            try:
                paid_users = User.objects.filter(
                    subscription__is_active=True,
                    subscription__is_trial=False
                )
            except Exception:
                paid_users = User.objects.none()
        
        if not paid_users.exists():
            self.stdout.write(self.style.WARNING('⚠️  No paid subscribers found'))
            self.stdout.write('   Signal alerts are only available for paid subscribers')
            self.stdout.write('   Activate subscription through admin panel or subscription page')
        else:
            self.stdout.write(self.style.SUCCESS(f'✅ Found {paid_users.count()} paid subscriber(s):'))
            for user in paid_users:
                alert_count = user.signal_alerts.filter(is_active=True).count()
                self.stdout.write(
                    f'   • {user.username} ({user.email}) - {alert_count} alert(s)'
                )
        
        # Test 4: Simulate signal notification
        self.stdout.write('\n🧪 Testing notification system...')
        
        test_signal = {
            'crypto': 'BTCUSD',
            'timeframe': '1h',
            'signal_type': 'SELL',
            'entry_price': 45100.00,
            'stop_loss': 45600.00,
            'target': 44200.00,
            'timestamp': timezone.now().strftime('%Y-%m-%d %H:%M:%S UTC'),
        }
        
        notifications_sent = notify_signal_subscribers(test_signal)
        
        if notifications_sent > 0:
            self.stdout.write(
                self.style.SUCCESS(f'✅ Sent {notifications_sent} notification(s) for BTCUSD 1h SELL signal')
            )
        else:
            self.stdout.write(
                self.style.WARNING('⚠️  No notifications sent (no matching alerts or paid subscribers)')
            )
        
        self.stdout.write(self.style.SUCCESS('\n✅ Signal alert test completed!\n'))
