#!/usr/bin/env python3
"""
Delete violations using Django ORM (most reliable method).
This will definitely work.

USAGE ON SERVER:
cd ~/smartrisk
sudo docker-compose exec django python delete_violations_orm.py
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'neuraltrade.settings')
django.setup()

from reversal_zones.models import ReversalZone

print("=" * 80)
print("🗑️ DELETING SPECIFIC VIOLATIONS USING DJANGO ORM")
print("=" * 80)

# Delete the exact violations identified
violations = [
    {'id': 2775, 'label': 'SELL', 'time': '2026-05-20 07:25:00'},
    {'id': 2776, 'label': 'BUY', 'time': '2026-05-20 14:10:00'},
]

print("\nViolations to delete:")
for v in violations:
    print(f"  - ID {v['id']}: {v['label']} at {v['time']}")

print("\n🗑️ Deleting...")

deleted_count = 0
for v in violations:
    try:
        signal = ReversalZone.objects.get(id=v['id'])
        signal_info = f"ID {signal.id}: {signal.label_text} at {signal.reversal_time}"
        signal.delete()
        print(f"   ✅ Deleted {signal_info}")
        deleted_count += 1
    except ReversalZone.DoesNotExist:
        print(f"   ⚠️ ID {v['id']} not found (already deleted?)")
    except Exception as e:
        print(f"   ❌ Error deleting ID {v['id']}: {e}")

print(f"\n✅ Deleted {deleted_count} violations")

# Verify - show remaining BTCUSD 5M signals
print("\n" + "=" * 80)
print("📋 REMAINING BTCUSD 5M SIGNALS (Last 24 Hours):")
print("=" * 80)

from datetime import datetime, timedelta
import pytz

cutoff = datetime.now(pytz.UTC) - timedelta(hours=24)

signals = ReversalZone.objects.filter(
    symbol='BTCUSDT',
    timeframe='5m',
    reversal_time__gte=cutoff
).order_by('reversal_time')

prev_label = None
violation_count = 0

for sig in signals:
    is_violation = prev_label == sig.label_text
    status = "❌ VIOLATION" if is_violation else "✅"
    
    print(f"{status} {sig.reversal_time.strftime('%Y-%m-%d %H:%M:%S')} - {sig.label_text} (ID: {sig.id})")
    
    if is_violation:
        violation_count += 1
    
    prev_label = sig.label_text

if violation_count == 0:
    print("\n✅ NO VIOLATIONS! Database is clean.")
else:
    print(f"\n❌ Still {violation_count} violations found!")

print("=" * 80)
print("✅ DONE! Refresh dashboard with Ctrl+Shift+R")
print("=" * 80)
