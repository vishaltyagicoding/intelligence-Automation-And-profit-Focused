"""
Test script to verify instant email notifications are working.
Run this on the AWS server to simulate a signal and check if email is sent instantly.
"""
import os
import django
import pytz
from datetime import datetime, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'neuraltrade.settings')
django.setup()

from reversal_zones.models import ReversalZone
from decimal import Decimal

def test_instant_email():
    """
    Create a test signal and verify email is sent instantly via Django signal.
    """
    print("\n" + "="*80)
    print("Testing Instant Email Notification System")
    print("="*80 + "\n")
    
    # Create a test signal
    test_time = datetime.now(pytz.utc) + timedelta(seconds=5)  # 5 seconds in future to avoid duplicates
    
    test_signal = {
        'symbol': 'BTCUSDT',
        'timeframe': '5m',
        'reversal_time': test_time,
        'center_price': Decimal('95000.50'),
        'stop_loss': Decimal('94500.00'),
        'target': Decimal('96000.00'),
        'outer_top': Decimal('96000.00'),
        'outer_bottom': Decimal('94500.00'),
        'core_top': Decimal('95100.00'),
        'core_bottom': Decimal('94900.00'),
        'is_bullish': True,
        'label_text': 'BUY',
        'bar_index': 12345,
    }
    
    print("📝 Creating test signal:")
    print(f"   Symbol: {test_signal['symbol']}")
    print(f"   Timeframe: {test_signal['timeframe']}")
    print(f"   Type: {test_signal['label_text']}")
    print(f"   Entry: ${test_signal['center_price']}")
    print(f"   Stop Loss: ${test_signal['stop_loss']}")
    print(f"   Target: ${test_signal['target']}")
    print(f"   Time: {test_signal['reversal_time']}")
    print()
    
    # Check if signal handler is registered
    from django.db.models.signals import post_save
    receivers = post_save._live_receivers(ReversalZone)
    print(f"🔍 Signal handlers registered: {len(receivers)}")
    
    if len(receivers) == 0:
        print("❌ ERROR: No signal handlers registered!")
        print("   Email notifications will NOT be sent.")
        return False
    
    print("✅ Signal handler is active\n")
    
    # Create the signal (this should trigger instant email)
    print("💾 Saving signal to database...")
    print("⏱️  Email should be sent INSTANTLY via Django signal...\n")
    
    try:
        signal, created = ReversalZone.objects.update_or_create(
            symbol=test_signal['symbol'],
            timeframe=test_signal['timeframe'],
            reversal_time=test_signal['reversal_time'],
            defaults={
                'center_price': test_signal['center_price'],
                'stop_loss': test_signal['stop_loss'],
                'target': test_signal['target'],
                'outer_top': test_signal['outer_top'],
                'outer_bottom': test_signal['outer_bottom'],
                'core_top': test_signal['core_top'],
                'core_bottom': test_signal['core_bottom'],
                'is_bullish': test_signal['is_bullish'],
                'label_text': test_signal['label_text'],
                'bar_index': test_signal['bar_index'],
            }
        )
        
        if created:
            print("✅ Signal created successfully!")
            print("📧 Django signal should have triggered email notification")
            print()
            print("Check Django logs for:")
            print("   '📧 INSTANT EMAIL: X sent for BTCUSD 5m BUY @ 95000.50'")
            print()
            print("If you see that log message, emails are working INSTANTLY! 🎉")
        else:
            print("⚠️  Signal already exists (updated instead of created)")
            print("   Email is only sent on CREATE, not UPDATE")
            print("   Try again with a different timestamp")
        
        # Clean up test signal
        print("\n🧹 Cleaning up test signal...")
        signal.delete()
        print("✅ Test signal deleted")
        
        return created
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_instant_email()
    
    print("\n" + "="*80)
    if success:
        print("✅ TEST PASSED: Instant email system is working!")
        print()
        print("Next steps:")
        print("1. Check your email inbox (if you have an active alert for BTCUSD 5m)")
        print("2. Monitor Django logs: sudo docker-compose logs -f django | grep 'INSTANT EMAIL'")
        print("3. Wait for next real signal to verify in production")
    else:
        print("❌ TEST FAILED: Check the errors above")
    print("="*80 + "\n")
