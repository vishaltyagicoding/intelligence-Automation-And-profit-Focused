#!/usr/bin/env python3
"""
COMPREHENSIVE FIX: Remove ALL violations from ALL cryptos and ALL timeframes.
This script will clean the database completely.

USAGE ON SERVER:
cd ~/smartrisk
sudo docker-compose exec django python fix_all_violations_comprehensive.py
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
print("🔍 COMPREHENSIVE VIOLATION CHECK AND FIX")
print("=" * 80)

# All symbols and timeframes
SYMBOLS = ['BTCUSDT', 'ETHUSDT', 'PAXGUSDT', 'LTCUSDT']
TIMEFRAMES = ['5m', '15m', '30m', '1h', '2h', '4h', '1d']

# Check last 60 days
cutoff_date = datetime.now(pytz.UTC) - timedelta(days=60)

total_signals = 0
total_violations = 0
total_deleted = 0

print("\n📊 SCANNING ALL CRYPTOS AND TIMEFRAMES...")
print("=" * 80)

for symbol in SYMBOLS:
    symbol_violations = 0
    
    for timeframe in TIMEFRAMES:
        # Get ALL signals for this symbol/timeframe
        signals = list(ReversalZone.objects.filter(
            symbol=symbol,
            timeframe=timeframe,
            reversal_time__gte=cutoff_date
        ).order_by('reversal_time').values('id', 'reversal_time', 'label_text', 'center_price'))
        
        if not signals:
            continue
        
        total_signals += len(signals)
        
        # Find violations
        violations_to_delete = []
        prev_signal = None
        
        for sig in signals:
            if prev_signal and prev_signal['label_text'] == sig['label_text']:
                violations_to_delete.append(sig['id'])
                total_violations += 1
                symbol_violations += 1
            prev_signal = sig
        
        # Delete violations
        if violations_to_delete:
            print(f"\n❌ {symbol} {timeframe}: {len(violations_to_delete)} violations")
            for vid in violations_to_delete:
                try:
                    ReversalZone.objects.filter(id=vid).delete()
                    total_deleted += 1
                    print(f"   ✅ Deleted ID: {vid}")
                except Exception as e:
                    print(f"   ❌ Error deleting ID {vid}: {e}")
    
    if symbol_violations > 0:
        print(f"\n📊 {symbol}: Deleted {symbol_violations} violations")

print("\n" + "=" * 80)
print(f"✅ CLEANUP COMPLETE!")
print(f"   Total signals scanned: {total_signals}")
print(f"   Total violations found: {total_violations}")
print(f"   Total signals deleted: {total_deleted}")
print("=" * 80)

# Verify - show all signals for last 24 hours
print("\n📋 VERIFICATION - ALL SIGNALS (Last 24 Hours):")
print("=" * 80)

cutoff_24h = datetime.now(pytz.UTC) - timedelta(hours=24)

for symbol in SYMBOLS:
    has_signals = False
    
    for timeframe in TIMEFRAMES:
        signals = ReversalZone.objects.filter(
            symbol=symbol,
            timeframe=timeframe,
            reversal_time__gte=cutoff_24h
        ).order_by('reversal_time')
        
        if signals.count() == 0:
            continue
        
        if not has_signals:
            print(f"\n{symbol}:")
            has_signals = True
        
        print(f"  {timeframe}: {signals.count()} signals")
        
        # Check for violations
        prev_label = None
        has_violation = False
        
        for sig in signals:
            if prev_label == sig.label_text:
                has_violation = True
                print(f"    ❌ VIOLATION STILL EXISTS: {sig.label_text} after {prev_label} at {sig.reversal_time}")
            prev_label = sig.label_text
        
        if not has_violation:
            print(f"    ✅ All signals alternate correctly")

print("\n" + "=" * 80)
print("✅ DONE!")
print("\nNext steps:")
print("1. Refresh dashboard with Ctrl+Shift+R")
print("2. Check all cryptos and timeframes")
print("3. All violations should be GONE")
print("=" * 80)
