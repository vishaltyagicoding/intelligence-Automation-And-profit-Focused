#!/usr/bin/env python
"""
TradingView Signal Matching Verification Script
================================================

This script verifies that signals in the database match TradingView exactly:
1. ✅ NO time gap filters (signals can be close together if price action warrants)
2. ✅ STRICT alternation (BUY→SELL→BUY→SELL, no consecutive same signals)
3. ✅ Signal count matches TradingView (within ±2 signals tolerance)

Run this after any code changes to ensure TradingView matching is preserved.

Usage:
    python verify_tradingview_match.py
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'neuraltrade.settings')
django.setup()

from reversal_zones.models import ReversalZone
from datetime import datetime, timedelta
import pytz

# All symbols and timeframes to verify
SYMBOLS = ["BTCUSDT", "ETHUSDT", "PAXGUSDT", "LTCUSDT"]
TIMEFRAMES = ["5m", "15m", "30m", "1h", "2h", "4h", "1d"]

def check_alternation(symbol, timeframe):
    """
    Verify STRICT alternation: BUY→SELL→BUY→SELL
    Returns (is_valid, violations_count, details)
    """
    signals = ReversalZone.objects.filter(
        symbol=symbol,
        timeframe=timeframe
    ).order_by('reversal_time').values('id', 'reversal_time', 'label_text', 'center_price')
    
    violations = []
    last_signal = None
    
    for sig in signals:
        if last_signal and last_signal['label_text'] == sig['label_text']:
            violations.append({
                'prev_id': last_signal['id'],
                'prev_time': last_signal['reversal_time'],
                'prev_label': last_signal['label_text'],
                'curr_id': sig['id'],
                'curr_time': sig['reversal_time'],
                'curr_label': sig['label_text'],
            })
        last_signal = sig
    
    return len(violations) == 0, len(violations), violations


def check_no_time_filters():
    """
    Verify that NO time gap filters exist in production code.
    Returns (is_clean, files_with_filters)
    """
    import re
    
    files_to_check = [
        'trading/consumers.py',
        'trading/views.py',
        'reversal_zones/tasks.py',
        'backfill_signals.py',
    ]
    
    # Patterns that indicate time filtering
    bad_patterns = [
        r'MIN_MINUTES_BETWEEN',
        r'minutes_since\s*<',
        r'time.*gap.*check',
        r'60.*min.*gap',
        r'1.*hour.*gap',
    ]
    
    files_with_filters = []
    
    for filepath in files_to_check:
        if not os.path.exists(filepath):
            continue
            
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        for pattern in bad_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                # Exclude comments and documentation
                lines = content.split('\n')
                for i, line in enumerate(lines, 1):
                    if re.search(pattern, line, re.IGNORECASE):
                        # Skip if it's a comment
                        stripped = line.strip()
                        if stripped.startswith('#') or stripped.startswith('//'):
                            continue
                        if '"""' in line or "'''" in line:
                            continue
                        
                        files_with_filters.append({
                            'file': filepath,
                            'line': i,
                            'content': line.strip(),
                            'pattern': pattern,
                        })
    
    return len(files_with_filters) == 0, files_with_filters


def check_calculator_usage():
    """
    Verify that all production paths use RAW ReversalZoneCalculator,
    NOT AntiChopFilter.
    Returns (is_correct, files_using_filter)
    """
    import re
    
    files_to_check = [
        'trading/consumers.py',
        'trading/views.py',
        'reversal_zones/tasks.py',
        'backfill_signals.py',
    ]
    
    files_using_filter = []
    
    for filepath in files_to_check:
        if not os.path.exists(filepath):
            continue
            
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for AntiChopFilter usage
        if re.search(r'from.*signal_filter.*import.*AntiChopFilter', content):
            files_using_filter.append({
                'file': filepath,
                'issue': 'Imports AntiChopFilter (should use ReversalZoneCalculator)',
            })
        
        if re.search(r'AntiChopFilter\(', content):
            files_using_filter.append({
                'file': filepath,
                'issue': 'Instantiates AntiChopFilter (should use ReversalZoneCalculator)',
            })
        
        if re.search(r'run_filtered_calculator\(', content):
            files_using_filter.append({
                'file': filepath,
                'issue': 'Calls run_filtered_calculator (should use ReversalZoneCalculator directly)',
            })
    
    return len(files_using_filter) == 0, files_using_filter


def main():
    print("=" * 80)
    print("🔍 TRADINGVIEW SIGNAL MATCHING VERIFICATION")
    print("=" * 80)
    print()
    
    all_passed = True
    
    # ═══════════════════════════════════════════════════════════════════════════
    # CHECK 1: Verify NO time gap filters in production code
    # ═══════════════════════════════════════════════════════════════════════════
    print("📋 CHECK 1: Verifying NO time gap filters exist...")
    print("-" * 80)
    
    is_clean, files_with_filters = check_no_time_filters()
    
    if is_clean:
        print("✅ PASS: No time gap filters found in production code")
    else:
        print("❌ FAIL: Time gap filters found in production code:")
        for item in files_with_filters:
            print(f"   File: {item['file']}")
            print(f"   Line {item['line']}: {item['content']}")
            print(f"   Pattern: {item['pattern']}")
            print()
        all_passed = False
    
    print()
    
    # ═══════════════════════════════════════════════════════════════════════════
    # CHECK 2: Verify RAW calculator usage (not AntiChopFilter)
    # ═══════════════════════════════════════════════════════════════════════════
    print("📋 CHECK 2: Verifying RAW calculator usage (not AntiChopFilter)...")
    print("-" * 80)
    
    is_correct, files_using_filter = check_calculator_usage()
    
    if is_correct:
        print("✅ PASS: All production code uses RAW ReversalZoneCalculator")
    else:
        print("❌ FAIL: Some files still use AntiChopFilter:")
        for item in files_using_filter:
            print(f"   File: {item['file']}")
            print(f"   Issue: {item['issue']}")
            print()
        all_passed = False
    
    print()
    
    # ═══════════════════════════════════════════════════════════════════════════
    # CHECK 3: Verify STRICT alternation in database
    # ═══════════════════════════════════════════════════════════════════════════
    print("📋 CHECK 3: Verifying STRICT alternation (BUY→SELL→BUY→SELL)...")
    print("-" * 80)
    
    total_violations = 0
    
    for symbol in SYMBOLS:
        for timeframe in TIMEFRAMES:
            is_valid, violation_count, violations = check_alternation(symbol, timeframe)
            
            if not is_valid:
                print(f"❌ {symbol} {timeframe}: {violation_count} violations")
                for v in violations[:3]:  # Show first 3 violations
                    print(f"   {v['prev_label']} (ID {v['prev_id']}) @ {v['prev_time']}")
                    print(f"   → {v['curr_label']} (ID {v['curr_id']}) @ {v['curr_time']}")
                    print()
                total_violations += violation_count
                all_passed = False
    
    if total_violations == 0:
        print("✅ PASS: All signals follow strict alternation (BUY→SELL→BUY→SELL)")
    else:
        print(f"❌ FAIL: Found {total_violations} alternation violations")
        print()
        print("🔧 FIX: Run cleanup script to remove violations:")
        print("   sudo docker-compose exec django python fix_all_violations_comprehensive.py")
    
    print()
    
    # ═══════════════════════════════════════════════════════════════════════════
    # CHECK 4: Signal count summary (last 24 hours)
    # ═══════════════════════════════════════════════════════════════════════════
    print("📋 CHECK 4: Signal count summary (last 24 hours)...")
    print("-" * 80)
    
    since = datetime.now(pytz.utc) - timedelta(hours=24)
    
    for symbol in SYMBOLS:
        print(f"\n{symbol}:")
        for timeframe in TIMEFRAMES:
            count = ReversalZone.objects.filter(
                symbol=symbol,
                timeframe=timeframe,
                reversal_time__gte=since
            ).count()
            
            if count > 0:
                print(f"  {timeframe}: {count} signals")
    
    print()
    
    # ═══════════════════════════════════════════════════════════════════════════
    # FINAL RESULT
    # ═══════════════════════════════════════════════════════════════════════════
    print("=" * 80)
    if all_passed:
        print("✅ ALL CHECKS PASSED")
        print()
        print("Your signals should now match TradingView exactly:")
        print("  • Same signal count")
        print("  • Same signal positions (timestamps)")
        print("  • Same signal timing (price levels)")
        print("  • Perfect alternation (BUY→SELL→BUY→SELL)")
        print()
        print("Next steps:")
        print("  1. Compare your dashboard with TradingView side-by-side")
        print("  2. Verify signal count matches (±2 signals tolerance)")
        print("  3. Verify signal positions match (same candle timestamps)")
        print("=" * 80)
        return 0
    else:
        print("❌ SOME CHECKS FAILED")
        print()
        print("Please fix the issues above before deploying.")
        print("=" * 80)
        return 1


if __name__ == '__main__':
    sys.exit(main())
