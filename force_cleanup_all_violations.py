#!/usr/bin/env python3
"""
AGGRESSIVE cleanup - removes ALL alternation violations from database.
This script is more thorough and will definitely clean everything.

USAGE ON SERVER:
cd ~/smartrisk
sudo docker-compose exec django python force_cleanup_all_violations.py
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
print("🗑️ AGGRESSIVE CLEANUP - REMOVING ALL ALTERNATION VIOLATIONS")
print("=" * 80)

# Clean up ALL signals (not just recent) - go back 60 days
cutoff_date = datetime.now(pytz.UTC) - timedelta(days=60)

total_violations = 0
total_deleted = 0

for symbol in SYMBOLS:
    print(f"\n{'=' * 80}")
    print(f"Processing: {symbol}")
    print('=' * 80)
    
    for timeframe in TIMEFRAMES:
        # Get ALL signals for this symbol/timeframe (last 60 days)
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
                print(f"   ❌ VIOLATION: {sig.label_text} after {prev_signal.label_text} at {sig.reversal_time.strftime('%Y-%m-%d %H:%M:%S')} (ID: {sig.id})")
                total_violations += 1
            prev_signal = sig
        
        # Delete violations ONE BY ONE (more reliable)
        if violations:
            print(f"   🗑️ Deleting {len(violations)} violations...")
            for sig in violations:
                try:
                    sig_id = sig.id
                    sig_time = sig.reversal_time.strftime('%Y-%m-%d %H:%M:%S')
                    sig_label = sig.label_text
                    sig.delete()
                    total_deleted += 1
                    print(f"      ✅ Deleted: {sig_label} at {sig_time} (ID: {sig_id})")
                except Exception as e:
                    print(f"      ❌ Error deleting signal ID {sig.id}: {e}")
        else:
            print(f"   ✅ No violations found")

print("\n" + "=" * 80)
print(f"✅ CLEANUP COMPLETE!")
print(f"   Total violations found: {total_violations}")
print(f"   Total signals deleted: {total_deleted}")
print("=" * 80)

# Verify cleanup - show remaining signals for last 24 hours
print("\n📋 VERIFICATION - REMAINING SIGNALS (Last 24 Hours):")
print("=" * 80)

today = datetime.now(pytz.UTC) - timedelta(hours=24)

for symbol in SYMBOLS:
    has_signals = False
    
    for timeframe in TIMEFRAMES:
        signals = ReversalZone.objects.filter(
            symbol=symbol,
            timeframe=timeframe,
            reversal_time__gte=today
        ).order_by('reversal_time')
        
        if signals.count() == 0:
            continue
        
        if not has_signals:
            print(f"\n{symbol}:")
            has_signals = True
        
        print(f"  {timeframe}:")
        prev_label = None
        all_good = True
        
        for sig in signals:
            status = "✅" if prev_label != sig.label_text else "❌"
            print(f"    {status} {sig.reversal_time.strftime('%Y-%m-%d %H:%M:%S')} - {sig.label_text} (ID: {sig.id})")
            
            if prev_label == sig.label_text:
                all_good = False
                print(f"       ⚠️ WARNING: Still a violation! This should not happen!")
            
            prev_label = sig.label_text
        
        if all_good:
            print(f"    ✅ All signals alternate correctly!")

print("\n" + "=" * 80)
print("✅ DONE!")
print("\nNext steps:")
print("1. Refresh dashboard: https://smartriskfx.com/dashboard")
print("2. Check all cryptos and timeframes")
print("3. Verify signals alternate: BUY → SELL → BUY → SELL")
print("=" * 80)
