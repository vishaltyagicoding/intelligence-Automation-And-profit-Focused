"""
Test Stop Loss Calculation
===========================
Verify the Stop Loss calculation logic is correct
"""

def calculate_stop_loss(entry, target, signal_type):
    """Calculate stop loss based on distance between entry and target"""
    try:
        entry_float = float(entry)
        target_float = float(target)
        
        if signal_type == 'BUY':
            # For BUY: Calculate distance and go 50% down from entry
            # Distance = Target - Entry
            # Stop Loss = Entry - (Distance * 0.5)
            calculate_distance = target_float - entry_float
            stop_loss_value = entry_float - (calculate_distance * 0.5)
            return f"{stop_loss_value:.2f}"
        elif signal_type == 'SELL':
            # For SELL: Calculate distance and go 50% up from entry
            # Distance = Entry - Target
            # Stop Loss = Entry + (Distance * 0.5)
            calculate_distance = entry_float - target_float
            stop_loss_value = entry_float + (calculate_distance * 0.5)
            return f"{stop_loss_value:.2f}"
    except (ValueError, TypeError):
        return 'N/A'
    
    return 'N/A'


# Test Case 1: BUY Signal
print("=" * 60)
print("TEST CASE 1: BUY Signal")
print("=" * 60)
entry = 50000.00
target = 52000.00
signal_type = 'BUY'
distance = target - entry
expected_stop_loss = entry - (distance * 0.5)
stop_loss = calculate_stop_loss(entry, target, signal_type)

print(f"Entry Price: ${entry:,.2f}")
print(f"Target Price: ${target:,.2f}")
print(f"Distance: ${distance:,.2f}")
print(f"Stop Loss: ${float(stop_loss):,.2f}")
print(f"Expected: ${expected_stop_loss:,.2f} (50% down from distance)")
print(f"✅ PASS" if float(stop_loss) == expected_stop_loss else f"❌ FAIL")
print()

# Test Case 2: SELL Signal
print("=" * 60)
print("TEST CASE 2: SELL Signal")
print("=" * 60)
entry = 3000.00
target = 2800.00
signal_type = 'SELL'
distance = entry - target
expected_stop_loss = entry + (distance * 0.5)
stop_loss = calculate_stop_loss(entry, target, signal_type)

print(f"Entry Price: ${entry:,.2f}")
print(f"Target Price: ${target:,.2f}")
print(f"Distance: ${distance:,.2f}")
print(f"Stop Loss: ${float(stop_loss):,.2f}")
print(f"Expected: ${expected_stop_loss:,.2f} (50% up from distance)")
print(f"✅ PASS" if float(stop_loss) == expected_stop_loss else f"❌ FAIL")
print()

# Test Case 3: Another BUY Signal
print("=" * 60)
print("TEST CASE 3: BUY Signal (Different Values)")
print("=" * 60)
entry = 100.00
target = 120.00
signal_type = 'BUY'
distance = target - entry
expected_stop_loss = entry - (distance * 0.5)
stop_loss = calculate_stop_loss(entry, target, signal_type)

print(f"Entry Price: ${entry:,.2f}")
print(f"Target Price: ${target:,.2f}")
print(f"Distance: ${distance:,.2f}")
print(f"Stop Loss: ${float(stop_loss):,.2f}")
print(f"Expected: ${expected_stop_loss:,.2f} (50% down from distance)")
print(f"✅ PASS" if float(stop_loss) == expected_stop_loss else f"❌ FAIL")
print()

# Test Case 4: Another SELL Signal
print("=" * 60)
print("TEST CASE 4: SELL Signal (Different Values)")
print("=" * 60)
entry = 200.00
target = 180.00
signal_type = 'SELL'
distance = entry - target
expected_stop_loss = entry + (distance * 0.5)
stop_loss = calculate_stop_loss(entry, target, signal_type)

print(f"Entry Price: ${entry:,.2f}")
print(f"Target Price: ${target:,.2f}")
print(f"Distance: ${distance:,.2f}")
print(f"Stop Loss: ${float(stop_loss):,.2f}")
print(f"Expected: ${expected_stop_loss:,.2f} (50% up from distance)")
print(f"✅ PASS" if float(stop_loss) == expected_stop_loss else f"❌ FAIL")
print()

print("=" * 60)
print("ALL TESTS COMPLETED")
print("=" * 60)
