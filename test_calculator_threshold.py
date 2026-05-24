#!/usr/bin/env python
"""
Test if calculator threshold matches Pine Script exactly.

Pine Script threshold calculation:
    presetPct = 0.015  (for "Low")
    presetATR = 2.8    (for "Low")
    customAbs = 0.05
    
    reversalThreshold = math.max(
        close * presetPct / 100.0,
        math.max(customAbs, presetATR * atrNow)
    )

CRITICAL: Pine Script divides by 100.0 AGAIN after multiplying by presetPct!
So: close * 0.015 / 100.0 = close * 0.00015 (0.015% of price)

For BTC @ $77,000:
    - close * 0.015 / 100 = 77000 * 0.00015 = $11.55
    - customAbs = $0.05
    - ATR * 2.8 = assume ATR=$200, so 2.8 * 200 = $560
    
    threshold = max($11.55, max($0.05, $560)) = $560
"""

# Test with BTC values from screenshot
close_btc = 77000.0
atr_btc = 200.0  # Typical ATR for BTC

# Pine Script values
preset_pct = 0.015
preset_atr = 2.8
custom_abs = 0.05

# Calculate threshold
pct_component = close_btc * preset_pct / 100.0
abs_component = custom_abs
atr_component = preset_atr * atr_btc

threshold = max(pct_component, max(abs_component, atr_component))

print("=" * 80)
print("THRESHOLD CALCULATION TEST - BTC")
print("=" * 80)
print(f"\nInput:")
print(f"  Close: ${close_btc:,.2f}")
print(f"  ATR: ${atr_btc:.2f}")
print()
print(f"Components:")
print(f"  1. Percentage: {close_btc:,.2f} * {preset_pct} / 100 = ${pct_component:.2f}")
print(f"  2. Absolute: ${abs_component:.2f}")
print(f"  3. ATR-based: {preset_atr} * {atr_btc:.2f} = ${atr_component:.2f}")
print()
print(f"Final threshold: ${threshold:.2f}")
print(f"As % of price: {(threshold / close_btc) * 100:.3f}%")
print()
print("=" * 80)
print("CONCLUSION:")
print(f"BTC must move ${threshold:.2f} ({(threshold / close_btc) * 100:.2f}%) to trigger reversal")
print("=" * 80)
