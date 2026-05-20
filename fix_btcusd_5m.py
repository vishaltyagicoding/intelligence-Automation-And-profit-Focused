#!/usr/bin/env python3
"""
Fix BTCUSD 5M violations specifically.
This will show and remove the exact violations you're seeing on the chart.

USAGE ON SERVER:
cd ~/smartrisk
sudo docker-compose exec django python fix_btcusd_5m.py
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
print("🔍 CHECKING BTCUSD 5M SIGNALS (BTCUSDT in database)")
print("=" * 80)

# BTCUSD is stored as BTCUSDT in database
symbol = 'BTCUSDT'
timeframe = '5m'

# Get last 48 hours of signals
cutoff = datetime.now(pytz.UTC) - timedelta(hours=48)

signals = list(ReversalZone.objects.filter(
    symbol=symbol,
    timeframe=timeframe,
    reversal_time__gte=cutoff
).order_by('reversal_time').values('id', 'reversal_time', 'label_text', 'center_price'))

print(f"\nFound {len(signals)} signals in last 48 hours:")
print("=" * 80)

# Show all signals and identify violations
violations = []
prev_signal = None

for i, sig in enumerate(signals):
    is_violation = prev_signal and prev_signal['label_text'] == sig['label_text']
    
    if is_violation:
        status = "❌ VIOLATION"
        violations.append(sig)
    else:
        status = "✅"
    
    print(f"{i+1}. {status} {sig['reversal_time'].strftime('%Y-%m-%d %H:%M:%S')} - {sig['label_text']} (ID: {sig['id']}, Price: ${sig['center_price']:.2f})")
    
    if is_violation:
        print(f"   ⚠️ This is a {sig['label_text']} after {prev_signal['label_text']} - VIOLATION!")
    
    prev_signal = sig

print("\n" + "=" * 80)

if not violations:
    print("✅ NO VIOLATIONS FOUND!")
    print("The database is clean. If you still see violations on chart:")
    print("1. Hard refresh: Ctrl+Shift+R")
    print("2. Clear browser cache")
    print("3. Check if chart is loading from WebSocket (should be disabled)")
else:
    print(f"❌ FOUND {len(violations)} VIOLATIONS!")
    print("\nViolations to delete:")
    for v in violations:
        print(f"  - ID {v['id']}: {v['label_text']} at {v['reversal_time'].strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Ask for confirmation (auto-yes in script)
    print("\n🗑️ DELETING VIOLATIONS NOW...")
    
    deleted_count = 0
    with connection.cursor() as cursor:
        for v in violations:
            try:
                cursor.execute(
                    "DELETE FROM reversal_zones_reversalzone WHERE id = %s",
                    [v['id']]
                )
                print(f"   ✅ Deleted ID {v['id']}: {v['label_text']} at {v['reversal_time'].strftime('%Y-%m-%d %H:%M:%S')}")
                deleted_count += 1
            except Exception as e:
                print(f"   ❌ Error deleting ID {v['id']}: {e}")
    
    connection.commit()
    print(f"\n✅ Deleted {deleted_count} violations")
    
    # Show remaining signals
    print("\n" + "=" * 80)
    print("📋 REMAINING SIGNALS AFTER CLEANUP:")
    print("=" * 80)
    
    remaining = list(ReversalZone.objects.filter(
        symbol=symbol,
        timeframe=timeframe,
        reversal_time__gte=cutoff
    ).order_by('reversal_time').values('id', 'reversal_time', 'label_text', 'center_price'))
    
    prev_label = None
    for i, sig in enumerate(remaining):
        status = "✅" if prev_label != sig['label_text'] else "❌"
        print(f"{i+1}. {status} {sig['reversal_time'].strftime('%Y-%m-%d %H:%M:%S')} - {sig['label_text']} (ID: {sig['id']})")
        prev_label = sig['label_text']

print("\n" + "=" * 80)
print("✅ DONE!")
print("\nNext steps:")
print("1. Refresh dashboard: https://smartriskfx.com/dashboard")
print("2. Hard refresh: Ctrl+Shift+R (or Cmd+Shift+R)")
print("3. Select BTCUSD 5M chart")
print("4. Verify the two BUY signals in blue circle are GONE")
print("=" * 80)
