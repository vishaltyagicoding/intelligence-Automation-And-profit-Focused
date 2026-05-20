#!/usr/bin/env python3
"""
DIRECT SQL cleanup - uses raw SQL to forcefully remove violations.
This is the most aggressive approach and will definitely work.

USAGE ON SERVER:
cd ~/smartrisk
sudo docker-compose exec django python sql_force_cleanup.py
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'neuraltrade.settings')
django.setup()

from django.db import connection
from reversal_zones.models import ReversalZone
from datetime import datetime, timedelta
import pytz

print("=" * 80)
print("🗑️ DIRECT SQL CLEANUP - FORCEFULLY REMOVING ALL VIOLATIONS")
print("=" * 80)

# All symbols and timeframes
SYMBOLS = ['BTCUSDT', 'ETHUSDT', 'PAXGUSDT', 'LTCUSDT']
TIMEFRAMES = ['5m', '15m', '30m', '1h', '2h', '4h', '1d']

total_deleted = 0

for symbol in SYMBOLS:
    for timeframe in TIMEFRAMES:
        print(f"\n{'=' * 60}")
        print(f"Processing: {symbol} {timeframe}")
        print('=' * 60)
        
        # Get all signals for this symbol/timeframe, ordered by time
        signals = list(ReversalZone.objects.filter(
            symbol=symbol,
            timeframe=timeframe
        ).order_by('reversal_time').values('id', 'reversal_time', 'label_text', 'center_price'))
        
        if not signals:
            print("No signals found")
            continue
        
        print(f"Found {len(signals)} signals")
        
        # Find violations
        violations_to_delete = []
        prev_signal = None
        
        for sig in signals:
            if prev_signal and prev_signal['label_text'] == sig['label_text']:
                violations_to_delete.append(sig['id'])
                print(f"❌ VIOLATION: {sig['label_text']} after {prev_signal['label_text']} at {sig['reversal_time']}")
                print(f"   Will delete ID: {sig['id']}")
            prev_signal = sig
        
        # Delete violations using raw SQL (most reliable)
        if violations_to_delete:
            print(f"\n🗑️ Deleting {len(violations_to_delete)} violations using SQL...")
            
            with connection.cursor() as cursor:
                for vid in violations_to_delete:
                    try:
                        cursor.execute(
                            "DELETE FROM reversal_zones_reversalzone WHERE id = %s",
                            [vid]
                        )
                        print(f"   ✅ Deleted ID: {vid}")
                        total_deleted += 1
                    except Exception as e:
                        print(f"   ❌ Error deleting ID {vid}: {e}")
            
            # Commit the transaction
            connection.commit()
            print(f"✅ Committed {len(violations_to_delete)} deletions")
        else:
            print("✅ No violations found")

print("\n" + "=" * 80)
print(f"✅ SQL CLEANUP COMPLETE!")
print(f"   Total signals deleted: {total_deleted}")
print("=" * 80)

# Verify - show all signals for last 24 hours
print("\n📋 VERIFICATION - ALL SIGNALS (Last 24 Hours):")
print("=" * 80)

cutoff = datetime.now(pytz.UTC) - timedelta(hours=24)

for symbol in SYMBOLS:
    for timeframe in TIMEFRAMES:
        signals = ReversalZone.objects.filter(
            symbol=symbol,
            timeframe=timeframe,
            reversal_time__gte=cutoff
        ).order_by('reversal_time')
        
        if signals.count() == 0:
            continue
        
        print(f"\n{symbol} {timeframe}:")
        prev_label = None
        has_violation = False
        
        for sig in signals:
            status = "✅" if prev_label != sig.label_text else "❌ VIOLATION"
            print(f"  {status} {sig.reversal_time.strftime('%Y-%m-%d %H:%M:%S')} - {sig.label_text} (ID: {sig.id})")
            
            if prev_label == sig.label_text:
                has_violation = True
            
            prev_label = sig.label_text
        
        if not has_violation:
            print(f"  ✅ All signals alternate correctly!")

print("\n" + "=" * 80)
print("✅ DONE! Now:")
print("1. Refresh dashboard with Ctrl+Shift+R")
print("2. Check all cryptos and timeframes")
print("3. Violations should be GONE")
print("=" * 80)
