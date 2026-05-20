#!/usr/bin/env python3
"""
Direct cleanup script - run this on the server with Django environment loaded.

USAGE ON SERVER:
cd ~/smartrisk
sudo docker-compose exec django python run_cleanup_on_server.py
"""

import os
import django

# Setup Django
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

# Clean up ALL signals from last 30 days
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
        
        print(f"\n📊 {symbol} {timeframe}: Found {signals.count()} signals")
        
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

print("\n" + "=" * 80)
print(f"✅ CLEANUP COMPLETE!")
print(f"   Total violations found: {total_violations}")
print(f"   Total signals deleted: {total_deleted}")
print("=" * 80)

# Show remaining signals for verification (last 24 hours only)
print("\n📋 REMAINING SIGNALS - LAST 24 HOURS (should all alternate correctly):")
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
        
        print(f"\n{symbol} {timeframe}:")
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

print("\n" + "=" * 80)
print("✅ DONE! Refresh the dashboard to see clean signals.")
print("✅ Restart Celery to apply new alternation enforcement:")
print("   sudo docker-compose restart celery_beat celery_worker")
print("=" * 80)
