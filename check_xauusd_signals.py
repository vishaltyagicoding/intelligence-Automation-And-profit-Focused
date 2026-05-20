#!/usr/bin/env python3
"""
Check XAUUSD (PAXGUSDT) signals to see what's in the database.
This will show us exactly what the chart is displaying.

USAGE ON SERVER:
cd ~/smartrisk
sudo docker-compose exec django python check_xauusd_signals.py
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'neuraltrade.settings')
django.setup()

from reversal_zones.models import ReversalZone
from datetime import datetime, timedelta
import pytz

print("=" * 80)
print("🔍 CHECKING XAUUSD (PAXGUSDT) SIGNALS IN DATABASE")
print("=" * 80)

# Check last 7 days
cutoff_date = datetime.now(pytz.UTC) - timedelta(days=7)

# XAUUSD is stored as PAXGUSDT in database
symbol = 'PAXGUSDT'

# Check all timeframes
timeframes = ['5m', '15m', '30m', '1h', '2h', '4h', '1d']

for timeframe in timeframes:
    signals = ReversalZone.objects.filter(
        symbol=symbol,
        timeframe=timeframe,
        reversal_time__gte=cutoff_date
    ).order_by('reversal_time')
    
    if signals.count() == 0:
        continue
    
    print(f"\n{'=' * 80}")
    print(f"PAXGUSDT (XAUUSD) {timeframe}: {signals.count()} signals")
    print('=' * 80)
    
    prev_signal = None
    violation_count = 0
    
    for sig in signals:
        # Check if this is a violation
        is_violation = prev_signal and prev_signal.label_text == sig.label_text
        
        if is_violation:
            violation_count += 1
            status = "❌ VIOLATION"
        else:
            status = "✅"
        
        print(f"{status} {sig.reversal_time.strftime('%Y-%m-%d %H:%M:%S')} - {sig.label_text} (ID: {sig.id}, Price: {sig.center_price})")
        
        if is_violation:
            print(f"   ⚠️ {sig.label_text} after {prev_signal.label_text} - THIS IS THE BUG!")
        
        prev_signal = sig
    
    if violation_count == 0:
        print(f"\n✅ No violations in {timeframe}")
    else:
        print(f"\n❌ Found {violation_count} violations in {timeframe}")
        print(f"   These are the signals causing the blue circles on your chart!")

print("\n" + "=" * 80)
print("If you see violations above, run the aggressive cleanup:")
print("  sudo docker-compose exec django python force_cleanup_all_violations.py")
print("=" * 80)
