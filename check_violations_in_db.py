#!/usr/bin/env python3
"""
Check if there are any alternation violations in the database.
Run this on the server to verify the database is clean.

USAGE ON SERVER:
cd ~/smartrisk
sudo docker-compose exec django python check_violations_in_db.py
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
print("🔍 CHECKING DATABASE FOR ALTERNATION VIOLATIONS")
print("=" * 80)

# Check last 7 days
cutoff_date = datetime.now(pytz.UTC) - timedelta(days=7)

total_signals = 0
total_violations = 0
violations_by_crypto = {}

for symbol in SYMBOLS:
    crypto_violations = 0
    
    for timeframe in TIMEFRAMES:
        # Get signals for this symbol/timeframe (last 7 days)
        signals = ReversalZone.objects.filter(
            symbol=symbol,
            timeframe=timeframe,
            reversal_time__gte=cutoff_date
        ).order_by('reversal_time')
        
        if signals.count() == 0:
            continue
        
        total_signals += signals.count()
        
        # Check for alternation violations
        prev_signal = None
        violations = []
        
        for sig in signals:
            if prev_signal and prev_signal.label_text == sig.label_text:
                violations.append(sig)
                crypto_violations += 1
                total_violations += 1
            prev_signal = sig
        
        # Report violations for this symbol/timeframe
        if violations:
            print(f"\n❌ {symbol} {timeframe}: {len(violations)} violations")
            for sig in violations:
                print(f"   {sig.label_text} after {sig.label_text} at {sig.reversal_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    if crypto_violations > 0:
        violations_by_crypto[symbol] = crypto_violations

print("\n" + "=" * 80)
print("📊 SUMMARY (Last 7 Days)")
print("=" * 80)
print(f"Total signals checked: {total_signals}")
print(f"Total violations found: {total_violations}")

if total_violations == 0:
    print("\n✅ DATABASE IS CLEAN! No alternation violations found.")
    print("✅ All signals alternate correctly: BUY → SELL → BUY → SELL")
else:
    print(f"\n❌ Found {total_violations} violations across {len(violations_by_crypto)} cryptos:")
    for symbol, count in violations_by_crypto.items():
        print(f"   {symbol}: {count} violations")
    print("\n⚠️ Run cleanup script to remove these violations:")
    print("   sudo docker-compose exec django python run_cleanup_on_server.py")

print("=" * 80)
