#!/usr/bin/env python3
"""
Update Historical Signals with Strict Risk Management Rules
============================================================

This script recalculates stop loss and target for ALL existing ReversalZone records
to apply the new strict risk management constraints:

STOP LOSS: MINIMUM 0.2%, MAXIMUM 0.5% from entry
TARGET:    MINIMUM 0.4%, MAXIMUM 0.7% from entry

USAGE:
    # Dry run (preview changes without saving)
    python update_historical_risk_management.py --dry-run

    # Apply changes to database
    python update_historical_risk_management.py

    # Apply to specific symbol only
    python update_historical_risk_management.py --symbol BTCUSD

    # Apply to specific timeframe only
    python update_historical_risk_management.py --timeframe 15m
"""

import os
import sys
import django
import argparse
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'neuraltrade.settings')
django.setup()

from reversal_zones.models import ReversalZone
from django.db.models import Q


def apply_strict_constraints(entry_price: float, stop_loss: float, is_bullish: bool) -> tuple[float, float]:
    """
    Apply strict risk management constraints to stop loss and target.
    
    Args:
        entry_price: Entry price (center_price)
        stop_loss: Original stop loss price
        is_bullish: True for BUY, False for SELL
    
    Returns:
        (constrained_stop_loss, constrained_target)
    """
    # ── STRICT RISK MANAGEMENT CONSTANTS ─────────────────────────────────
    MIN_SL_PCT      = 0.002     # MINIMUM 0.2% stop loss
    MAX_SL_PCT      = 0.005     # MAXIMUM 0.5% stop loss
    MIN_TARGET_PCT  = 0.004     # MINIMUM 0.4% target
    MAX_TARGET_PCT  = 0.007     # MAXIMUM 0.7% target
    RISK_REWARD     = 2.5       # 2.5:1 risk-reward ratio
    
    if is_bullish:
        # ── BUY SIGNAL ────────────────────────────────────────────────────
        # Calculate stop loss distance as percentage
        sl_distance_pct = (entry_price - stop_loss) / entry_price
        
        # Enforce MINIMUM 0.2% stop loss
        if sl_distance_pct < MIN_SL_PCT:
            stop_loss = entry_price * (1 - MIN_SL_PCT)
            sl_distance_pct = MIN_SL_PCT
        
        # Enforce MAXIMUM 0.5% stop loss
        if sl_distance_pct > MAX_SL_PCT:
            stop_loss = entry_price * (1 - MAX_SL_PCT)
            sl_distance_pct = MAX_SL_PCT
        
        # Calculate risk
        risk = entry_price - stop_loss
        if risk <= 0:
            risk = entry_price * 0.003  # 0.3% fallback
        
        # Calculate target with 2.5:1 risk-reward
        rr_target = entry_price + (risk * RISK_REWARD)
        target_distance_pct = (rr_target - entry_price) / entry_price
        
        # Enforce MINIMUM 0.4% target
        if target_distance_pct < MIN_TARGET_PCT:
            target_distance_pct = MIN_TARGET_PCT
        
        # Enforce MAXIMUM 0.7% target
        if target_distance_pct > MAX_TARGET_PCT:
            target_distance_pct = MAX_TARGET_PCT
        
        # Calculate final target
        target = entry_price * (1 + target_distance_pct)
        
    else:
        # ── SELL SIGNAL ───────────────────────────────────────────────────
        # Calculate stop loss distance as percentage
        sl_distance_pct = (stop_loss - entry_price) / entry_price
        
        # Enforce MINIMUM 0.2% stop loss
        if sl_distance_pct < MIN_SL_PCT:
            stop_loss = entry_price * (1 + MIN_SL_PCT)
            sl_distance_pct = MIN_SL_PCT
        
        # Enforce MAXIMUM 0.5% stop loss
        if sl_distance_pct > MAX_SL_PCT:
            stop_loss = entry_price * (1 + MAX_SL_PCT)
            sl_distance_pct = MAX_SL_PCT
        
        # Calculate risk
        risk = stop_loss - entry_price
        if risk <= 0:
            risk = entry_price * 0.003  # 0.3% fallback
        
        # Calculate target with 2.5:1 risk-reward
        rr_target = entry_price - (risk * RISK_REWARD)
        target_distance_pct = (entry_price - rr_target) / entry_price
        
        # Enforce MINIMUM 0.4% target
        if target_distance_pct < MIN_TARGET_PCT:
            target_distance_pct = MIN_TARGET_PCT
        
        # Enforce MAXIMUM 0.7% target
        if target_distance_pct > MAX_TARGET_PCT:
            target_distance_pct = MAX_TARGET_PCT
        
        # Calculate final target
        target = entry_price * (1 - target_distance_pct)
    
    # Round to 2 decimal places
    stop_loss = round(stop_loss, 2)
    target = round(target, 2)
    
    return stop_loss, target


def main():
    parser = argparse.ArgumentParser(
        description='Update historical signals with strict risk management rules'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without saving to database'
    )
    parser.add_argument(
        '--symbol',
        type=str,
        help='Update only specific symbol (e.g., BTCUSD)'
    )
    parser.add_argument(
        '--timeframe',
        type=str,
        help='Update only specific timeframe (e.g., 15m)'
    )
    
    args = parser.parse_args()
    
    # Build query
    query = Q()
    if args.symbol:
        query &= Q(symbol=args.symbol.upper())
    if args.timeframe:
        query &= Q(timeframe=args.timeframe.lower())
    
    # Get all signals
    signals = ReversalZone.objects.filter(query).order_by('-reversal_time')
    total_count = signals.count()
    
    print("=" * 80)
    print("UPDATE HISTORICAL SIGNALS WITH STRICT RISK MANAGEMENT")
    print("=" * 80)
    print(f"Total signals to process: {total_count}")
    if args.symbol:
        print(f"Symbol filter: {args.symbol}")
    if args.timeframe:
        print(f"Timeframe filter: {args.timeframe}")
    print(f"Mode: {'DRY RUN (no changes)' if args.dry_run else 'LIVE (will update database)'}")
    print("=" * 80)
    print()
    
    if total_count == 0:
        print("❌ No signals found matching criteria")
        return
    
    # Confirm before proceeding
    if not args.dry_run:
        response = input(f"⚠️  This will update {total_count} signals. Continue? (yes/no): ")
        if response.lower() != 'yes':
            print("❌ Aborted by user")
            return
        print()
    
    # Process signals
    updated_count = 0
    skipped_count = 0
    error_count = 0
    
    for i, signal in enumerate(signals, 1):
        try:
            # Get current values
            entry = float(signal.center_price)
            old_sl = float(signal.stop_loss) if signal.stop_loss else (
                float(signal.outer_bottom) if signal.is_bullish else float(signal.outer_top)
            )
            old_target = float(signal.target) if signal.target else (
                float(signal.outer_top) if signal.is_bullish else float(signal.outer_bottom)
            )
            
            # Calculate new values with strict constraints
            new_sl, new_target = apply_strict_constraints(entry, old_sl, signal.is_bullish)
            
            # Calculate percentages
            old_sl_pct = abs(entry - old_sl) / entry * 100
            new_sl_pct = abs(entry - new_sl) / entry * 100
            old_target_pct = abs(old_target - entry) / entry * 100
            new_target_pct = abs(new_target - entry) / entry * 100
            
            # Check if update is needed
            if abs(new_sl - old_sl) < 0.01 and abs(new_target - old_target) < 0.01:
                skipped_count += 1
                if i % 50 == 0:
                    print(f"[{i}/{total_count}] Skipped (no change needed)")
                continue
            
            # Show changes
            signal_type = "BUY" if signal.is_bullish else "SELL"
            print(f"[{i}/{total_count}] {signal.symbol} {signal.timeframe} {signal_type} @ ${entry:,.2f}")
            print(f"  Stop Loss: ${old_sl:,.2f} ({old_sl_pct:.2f}%) → ${new_sl:,.2f} ({new_sl_pct:.2f}%)")
            print(f"  Target:    ${old_target:,.2f} ({old_target_pct:.2f}%) → ${new_target:,.2f} ({new_target_pct:.2f}%)")
            
            # Update database
            if not args.dry_run:
                signal.stop_loss = Decimal(str(new_sl))
                signal.target = Decimal(str(new_target))
                
                # Update outer_top and outer_bottom for consistency
                if signal.is_bullish:
                    signal.outer_bottom = Decimal(str(new_sl))
                    signal.outer_top = Decimal(str(new_target))
                else:
                    signal.outer_top = Decimal(str(new_sl))
                    signal.outer_bottom = Decimal(str(new_target))
                
                signal.save(update_fields=['stop_loss', 'target', 'outer_top', 'outer_bottom'])
                print(f"  ✅ Updated")
            else:
                print(f"  ℹ️  Would update (dry run)")
            
            print()
            updated_count += 1
            
        except Exception as e:
            error_count += 1
            print(f"[{i}/{total_count}] ❌ ERROR: {signal.symbol} {signal.timeframe} - {str(e)}")
            print()
    
    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total signals:   {total_count}")
    print(f"Updated:         {updated_count}")
    print(f"Skipped:         {skipped_count} (no change needed)")
    print(f"Errors:          {error_count}")
    print("=" * 80)
    
    if args.dry_run:
        print()
        print("ℹ️  This was a DRY RUN - no changes were saved")
        print("   Run without --dry-run to apply changes")
    else:
        print()
        print("✅ Database updated successfully!")
        print()
        print("Next steps:")
        print("1. Check signal history on website: https://smartriskfx.com/history")
        print("2. Verify stop loss values are between 0.2% - 0.5%")
        print("3. Verify target values are between 0.4% - 0.7%")


if __name__ == '__main__':
    main()
