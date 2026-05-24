#!/usr/bin/env python
"""
Diagnose why consecutive signals are still appearing.
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'neuraltrade.settings')
django.setup()

from reversal_zones.models import ReversalZone
from datetime import datetime, timedelta
import pytz

# Check BTCUSD 5m (from screenshot)
symbol = "BTCUSDT"
timeframe = "5m"

print("=" * 80)
print(f"DIAGNOSING CONSECUTIVE SIGNALS: {symbol} {timeframe}")
print("=" * 80)

# Get last 50 signals
signals = ReversalZone.objects.filter(
    symbol=symbol,
    timeframe=timeframe
).order_by('-reversal_time')[:50]

print(f"\nFound {signals.count()} signals in database")
print("\nLast 20 signals (newest first):")
print("-" * 80)

violations = []
prev_signal = None

for i, sig in enumerate(signals[:20], 1):
    time_str = sig.reversal_time.strftime("%Y-%m-%d %H:%M:%S")
    label = sig.label_text
    price = float(sig.center_price)
    
    # Check for consecutive same signals
    violation = ""
    if prev_signal and prev_signal['label'] == label:
        violation = " ⚠️ VIOLATION: Consecutive " + label
        violations.append({
            'prev_id': prev_signal['id'],
            'prev_time': prev_signal['time'],
            'prev_label': prev_signal['label'],
            'curr_id': sig.id,
            'curr_time': time_str,
            'curr_label': label,
        })
    
    print(f"{i:2d}. {time_str} - {label:4s} @ ${price:,.2f} (ID: {sig.id}){violation}")
    
    prev_signal = {
        'id': sig.id,
        'time': time_str,
        'label': label,
    }

print("\n" + "=" * 80)
print(f"TOTAL VIOLATIONS FOUND: {len(violations)}")
print("=" * 80)

if violations:
    print("\nVIOLATION DETAILS:")
    for v in violations:
        print(f"\n  Previous: {v['prev_label']} (ID {v['prev_id']}) @ {v['prev_time']}")
        print(f"  Current:  {v['curr_label']} (ID {v['curr_id']}) @ {v['curr_time']}")
        print(f"  ❌ This is a {v['curr_label']}→{v['curr_label']} violation")

print("\n" + "=" * 80)
print("NEXT STEPS:")
print("=" * 80)
if violations:
    print("1. Delete violation signals from database")
    print("2. Check why alternation enforcement failed")
    print("3. Fix the root cause in calculator or task")
else:
    print("✅ No violations found in database")
    print("The problem might be in the frontend display logic")
