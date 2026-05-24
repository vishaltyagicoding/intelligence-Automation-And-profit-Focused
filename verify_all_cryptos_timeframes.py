#!/usr/bin/env python
"""
Verify ALL cryptos and timeframes have no violations.
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'neuraltrade.settings')
django.setup()

from reversal_zones.models import ReversalZone
from datetime import datetime, timedelta
import pytz

SYMBOLS = ["BTCUSDT", "ETHUSDT", "PAXGUSDT", "LTCUSDT"]
TIMEFRAMES = ["5m", "15m", "30m", "1h", "2h", "4h", "1d"]

print("=" * 80)
print("🔍 VERIFYING ALL CRYPTOS AND TIMEFRAMES")
print("=" * 80)
print()

total_violations = 0
total_signals = 0

for symbol in SYMBOLS:
    print(f"\n{'='*80}")
    print(f"📊 {symbol}")
    print(f"{'='*80}")
    
    for timeframe in TIMEFRAMES:
        signals = ReversalZone.objects.filter(
            symbol=symbol,
            timeframe=timeframe
        ).order_by('reversal_time')
        
        count = signals.count()
        total_signals += count
        
        if count == 0:
            print(f"  {timeframe:4s}: No signals yet")
            continue
        
        # Check for violations
        violations = 0
        prev_label = None
        
        for sig in signals:
            if prev_label and prev_label == sig.label_text:
                violations += 1
                total_violations += 1
            prev_label = sig.label_text
        
        if violations > 0:
            print(f"  {timeframe:4s}: {count:3d} signals  ❌ {violations} VIOLATIONS")
        else:
            print(f"  {timeframe:4s}: {count:3d} signals  ✅ Perfect alternation")

print()
print("=" * 80)
print("📊 SUMMARY")
print("=" * 80)
print(f"Total signals: {total_signals}")
print(f"Total violations: {total_violations}")
print()

if total_violations == 0:
    print("✅ SUCCESS! All cryptos and timeframes have perfect alternation!")
    print()
    print("Your website is ready for 1000 users! 🎉")
else:
    print(f"❌ FAILURE! Found {total_violations} violations across all cryptos/timeframes")
    print()
    print("Next steps:")
    print("1. Check Celery logs for errors")
    print("2. Run clean_and_regenerate_all_signals.py")
    print("3. Contact support if issue persists")

print("=" * 80)
