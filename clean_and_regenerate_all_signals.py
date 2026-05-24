#!/usr/bin/env python
"""
NUCLEAR OPTION: Delete ALL signals and regenerate from scratch.

This ensures:
1. No duplicate signals from multiple task runs
2. Perfect alternation (calculator enforces it)
3. Clean slate matching TradingView exactly

WARNING: This will delete ALL existing signals!
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'neuraltrade.settings')
django.setup()

from reversal_zones.models import ReversalZone
from reversal_zones.tasks import calculate_all_history

print("=" * 80)
print("⚠️  NUCLEAR OPTION: CLEAN AND REGENERATE ALL SIGNALS")
print("=" * 80)
print()
print("This will:")
print("  1. DELETE all existing signals from database")
print("  2. Regenerate signals from scratch using raw calculator")
print("  3. Ensure perfect alternation (BUY→SELL→BUY→SELL)")
print()
print("⚠️  WARNING: This cannot be undone!")
print()

response = input("Type 'YES' to continue: ")
if response != 'YES':
    print("Aborted.")
    sys.exit(0)

print()
print("=" * 80)
print("STEP 1: Deleting all existing signals...")
print("=" * 80)

count_before = ReversalZone.objects.count()
print(f"Found {count_before} signals in database")

ReversalZone.objects.all().delete()

count_after = ReversalZone.objects.count()
print(f"✅ Deleted {count_before - count_after} signals")
print(f"Remaining: {count_after} signals")

print()
print("=" * 80)
print("STEP 2: Triggering full history recalculation...")
print("=" * 80)

result = calculate_all_history.apply_async()
print(f"✅ Task queued: {result.id}")

print()
print("=" * 80)
print("NEXT STEPS:")
print("=" * 80)
print("1. Wait 10 minutes for signals to regenerate")
print("2. Monitor Celery logs:")
print("   sudo docker-compose logs -f celery_worker | grep 'Signal saved'")
print()
print("3. Compare with TradingView:")
print("   - Your website: https://smartriskfx.com/dashboard")
print("   - TradingView: https://www.tradingview.com/chart/")
print()
print("4. Verify alternation:")
print("   python diagnose_consecutive_signals.py")
print("=" * 80)
