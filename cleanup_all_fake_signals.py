#!/usr/bin/env python3
"""
Clean up ALL fake signals (alternation violations) from database
This will remove BUY→BUY and SELL→SELL violations for ALL cryptos and ALL timeframes

USAGE:
1. SSH to server: ssh -i smartriskfx-singapore.pem ubuntu@13.250.19.107
2. Navigate to project: cd ~/smartrisk
3. Open Django shell: sudo docker-compose exec django python manage.py shell
4. Copy and paste the CLEANUP_SCRIPT below
5. Exit shell: exit()
6. Refresh dashboard to see clean signals
"""

CLEANUP_SCRIPT = """
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'neuraltrade.settings')
django.setup()

from reversal_zones.models import ReversalZone
from datetime import datetime, timedelta
import pytz

# All symbols and timeframes
SYMBOLS = ['BTCUSDT', 'ETHUSDT', 'PAXGUSDT', 'LTCUSDT']
TIMEFRAMES = ['5m', '15m', '30m', '1h', '2h', '4h', '1d']

print("=" * 80)
print("🗑️ CLEANING UP FAKE SIGNALS FOR ALL CRYPTOS AND TIMEFRAMES")
print("=" * 80)

# Clean up ALL signals (not just today) - go back 30 days
cutoff_date = datetime.now(pytz.UTC) - timedelta(days=30)

total_violations = 0
total_deleted = 0

for symbol in SYMBOLS:
    for timeframe in TIMEFRAMES:
        # Get ALL recent signals for this symbol/timeframe (last 30 days)
        signals = ReversalZone.objects.filter(
            symbol=symbol,
            timeframe=timeframe,
            reversal_time__gte=cutoff_date
        ).order_by('reversal_time')
        
        if signals.count() == 0:
            continue
        
        print(f"\\n📊 {symbol} {timeframe}: Found {signals.count()} signals")
        
        # Check for alternation violations
        prev_signal = None
        violations = []
        
        for sig in signals:
            if prev_signal and prev_signal.label_text == sig.label_text:
                violations.append(sig)
                print(f"   ❌ VIOLATION: {sig.label_text} after {prev_signal.label_text} at {sig.reversal_time.strftime('%Y-%m-%d %H:%M:%S')}")
                total_violations += 1
            prev_signal = sig
        
        # Delete violations
        if violations:
            for sig in violations:
                sig.delete()
                total_deleted += 1
            print(f"   ✅ Deleted {len(violations)} violating signals")

print("\\n" + "=" * 80)
print(f"✅ CLEANUP COMPLETE!")
print(f"   Total violations found: {total_violations}")
print(f"   Total signals deleted: {total_deleted}")
print("=" * 80)

# Show remaining signals for verification (last 24 hours only)
print("\\n📋 REMAINING SIGNALS - LAST 24 HOURS (should all alternate correctly):")
print("=" * 80)

today = datetime.now(pytz.UTC) - timedelta(hours=24)

for symbol in SYMBOLS:
    for timeframe in TIMEFRAMES:
        signals = ReversalZone.objects.filter(
            symbol=symbol,
            timeframe=timeframe,
            reversal_time__gte=today
        ).order_by('reversal_time')
        
        if signals.count() == 0:
            continue
        
        print(f"\\n{symbol} {timeframe}:")
        prev_label = None
        all_good = True
        
        for sig in signals:
            status = "✅" if prev_label != sig.label_text else "❌"
            print(f"   {status} {sig.reversal_time.strftime('%Y-%m-%d %H:%M:%S')} - {sig.label_text}")
            
            if prev_label == sig.label_text:
                all_good = False
            
            prev_label = sig.label_text
        
        if all_good:
            print(f"   ✅ All signals alternate correctly!")

print("\\n" + "=" * 80)
print("✅ DONE! Refresh the dashboard to see clean signals.")
print("=" * 80)
"""

if __name__ == "__main__":
    print("=" * 80)
    print("CLEANUP SCRIPT FOR ALL CRYPTOS AND TIMEFRAMES")
    print("=" * 80)
    print()
    print("Run these commands on the server:")
    print()
    print("1. SSH to server:")
    print("   ssh -i smartriskfx-singapore.pem ubuntu@13.250.19.107")
    print()
    print("2. Navigate to project:")
    print("   cd ~/smartrisk")
    print()
    print("3. Open Django shell:")
    print("   sudo docker-compose exec django python manage.py shell")
    print()
    print("4. Paste this code:")
    print()
    print(CLEANUP_SCRIPT)
    print()
    print("5. Exit shell:")
    print("   exit()")
    print()
    print("6. Restart Celery to apply new alternation enforcement:")
    print("   sudo docker-compose restart celery_beat celery_worker")
    print()
    print("7. Refresh dashboard to see clean signals")
    print("=" * 80)
