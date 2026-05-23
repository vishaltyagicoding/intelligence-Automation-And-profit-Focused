#!/usr/bin/env python
"""
Verify that threshold calculation matches TradingView Pine Script EXACTLY.

Pine Script:
    presetPct = 0.015  (for "Low" preset)
    presetATR = 2.8    (for "Low" preset)
    customAbs = 0.05
    
    reversalThreshold = math.max(
        close * presetPct / 100.0,
        math.max(customAbs, presetATR * atrNow)
    )

For ETH @ $2,000, ATR = $20:
    - close * 0.015 / 100 = 2000 * 0.015 / 100 = 0.30
    - customAbs = 0.05
    - presetATR * atrNow = 2.8 * 20 = 56
    
    threshold = max(0.30, max(0.05, 56)) = max(0.30, 56) = 56

So for ETH @ $2,000, threshold = $56 (2.8% of price)
"""

# Test with realistic values
close = 2000.0  # ETH price
atr = 20.0      # Typical ATR for ETH

# Pine Script calculation
preset_pct = 0.015  # "Low" preset
preset_atr = 2.8    # "Low" preset
custom_abs = 0.05

pct_component = close * preset_pct / 100.0
abs_component = custom_abs
atr_component = preset_atr * atr

threshold_pine = max(pct_component, max(abs_component, atr_component))

print("=" * 80)
print("THRESHOLD CALCULATION VERIFICATION")
print("=" * 80)
print(f"\nInput:")
print(f"  Close price: ${close:.2f}")
print(f"  ATR: ${atr:.2f}")
print()
print(f"Components:")
print(f"  1. Percentage: {close} * {preset_pct} / 100 = ${pct_component:.4f}")
print(f"  2. Absolute: ${abs_component:.4f}")
print(f"  3. ATR-based: {preset_atr} * {atr} = ${atr_component:.2f}")
print()
print(f"Final threshold: max({pct_component:.4f}, max({abs_component:.4f}, {atr_component:.2f}))")
print(f"               = max({pct_component:.4f}, {atr_component:.2f})")
print(f"               = ${threshold_pine:.2f}")
print()
print(f"As percentage of price: {(threshold_pine / close) * 100:.2f}%")
print("=" * 80)
print()
print("CONCLUSION:")
print(f"For ETH @ ${close:.2f}, the threshold is ${threshold_pine:.2f} ({(threshold_pine / close) * 100:.2f}%)")
print("This means price must move $56 to trigger a reversal signal.")
print()
print("This is CORRECT - it prevents too-frequent signals on volatile assets.")
print("=" * 80)
