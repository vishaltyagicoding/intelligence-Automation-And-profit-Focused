# Universal Stop Loss & Target Calculation Fix - Bugfix Design

## Overview

The SmartRisk platform currently uses a naive percentage-based approach (2% stop loss, 4% target) for all cryptocurrency symbols, which fails to account for symbol price level differences and market structure. This design document specifies a universal calculation system that:

1. **Adapts to symbol characteristics**: High-priced symbols (XAUUSD $4,500+, BTCUSD $100,000+) use absolute point-based buffers, while low-priced symbols (ETHUSD $3,000, LTCUSD $100) use percentage-based buffers.
2. **Analyzes market structure**: Scans backwards to find the last bearish/bullish candle for stop loss placement, respecting actual price action.
3. **Applies ATR safety guards**: Ensures stop loss distances are realistic relative to market volatility (1.5× to 3.0× ATR).
4. **Uses 2:1 risk-reward ratio**: Calculates target as entry + (2 × risk) for consistent profitability expectations.
5. **Ensures data consistency**: Email alerts, history API, and WebSocket broadcasts all read from the same database source.

The fix modifies the `_professional_sl_target()` function in `reversal_zones/reversal_calculator.py` and ensures all display channels (history API, email alerts, WebSocket) read stop_loss and target values directly from the ReversalZone database records.

## Glossary

- **Bug_Condition (C)**: The condition that triggers incorrect stop loss/target calculations - when signals are generated using naive percentage-based logic that ignores symbol price levels and market structure
- **Property (P)**: The desired behavior - stop loss and target values calculated using universal logic that adapts to symbol characteristics, respects market structure, applies ATR safety guards, and uses 2:1 risk-reward ratio
- **Preservation**: Existing signal generation, anti-chop filtering, alternation enforcement, and WebSocket broadcasting behavior that must remain unchanged
- **ATR (Average True Range)**: A volatility indicator measuring the average price movement over 14 periods, used as a safety guard for stop loss distances
- **High-Priced Symbol**: Symbols with price > $1000 (XAUUSD, BTCUSD) that require absolute point-based buffers
- **Low-Priced Symbol**: Symbols with price ≤ $1000 (ETHUSD, LTCUSD) that require percentage-based buffers
- **Bearish Candle**: A candle where close < open (red candle), indicating downward price movement
- **Bullish Candle**: A candle where close > open (green candle), indicating upward price movement
- **Doji Candle**: A candle where |close - open| < 0.01% of price, indicating indecision (skipped in stop loss calculation)
- **Risk**: The distance between entry price and stop loss: Risk = |entry - stop_loss|
- **Risk-Reward Ratio**: The ratio of potential profit to potential loss, fixed at 2:1 (target distance = 2 × risk distance)
- **ReversalZone**: Django model storing signal data including symbol, timeframe, center_price, stop_loss, target, outer_top, outer_bottom, core_top, core_bottom, is_bullish, label_text, bar_index, reversal_time
- **_professional_sl_target()**: Function in reversal_calculator.py that calculates stop loss and target based on market structure and ATR safety guards

## Bug Details

### Bug Condition

The bug manifests when a signal is generated for any cryptocurrency symbol. The `_professional_sl_target()` function in `reversal_zones/reversal_calculator.py` currently uses a naive percentage-based approach that fails to account for symbol price level differences, market structure analysis, and ATR-based validation.

**Formal Specification:**
```
FUNCTION isBugCondition(input)
  INPUT: input of type SignalGenerationEvent with fields:
    - symbol: string (e.g., 'BTCUSDT', 'PAXGUSDT', 'ETHUSDT', 'LTCUSDT')
    - price: float (current entry price)
    - is_bullish: boolean (BUY or SELL signal)
    - timeframe: string (e.g., '15m', '1h', '4h')
  OUTPUT: boolean
  
  RETURN (
    # Condition 1: High-priced symbols with percentage-based logic
    (input.price > 1000 AND stop_loss_uses_percentage_logic(input))
    OR
    # Condition 2: Any symbol without market structure analysis
    (NOT scans_backwards_for_candle_structure(input))
    OR
    # Condition 3: Any symbol without ATR safety guards
    (NOT applies_atr_safety_guards(input))
    OR
    # Condition 4: Target not using 2:1 risk-reward ratio
    (NOT uses_2_to_1_risk_reward(input))
    OR
    # Condition 5: Email alerts calculate differently than database
    (email_stop_loss != database_stop_loss OR email_target != database_target)
  )
END FUNCTION
```

### Examples

**Example 1: High-Priced Symbol (XAUUSD at $4,569.30) - BUY Signal**
- **Current Behavior**: stop_loss = $4,569.30 × 0.98 = $4,477.91, target = $4,569.30 × 1.04 = $4,752.07
- **Problem**: Uses percentage-based logic for high-priced symbol, resulting in $91.39 risk and $182.77 reward (correct 2:1 ratio but ignores market structure)
- **Expected Behavior**: Scan backwards to find last bearish candle at $4,550 (moved 30 points), stop_loss = $4,550 - 20 = $4,530, risk = $39.30, target = $4,569.30 + (2 × $39.30) = $4,647.90

**Example 2: High-Priced Symbol (BTCUSD at $100,000) - SELL Signal**
- **Current Behavior**: stop_loss = $100,000 × 1.02 = $102,000, target = $100,000 × 0.96 = $96,000
- **Problem**: Uses percentage-based logic, resulting in $2,000 risk and $4,000 reward (correct 2:1 ratio but ignores market structure)
- **Expected Behavior**: Scan backwards to find last bullish candle at $99,800 (moved 25 points), stop_loss = $99,800 + 20 + 20 = $99,840, risk = $160, target = $100,000 - (2 × $160) = $99,680

**Example 3: Low-Priced Symbol (ETHUSD at $3,000) - BUY Signal**
- **Current Behavior**: stop_loss = $3,000 × 0.98 = $2,940, target = $3,000 × 1.04 = $3,120
- **Problem**: Uses percentage-based logic but calculations are inconsistent, resulting in duplicate database entries with different SL/TP values
- **Expected Behavior**: Scan backwards to find last bearish candle at $2,990 (moved $10 = 0.033% of entry), buffer = $10 + ($3,000 × 0.0003) = $10.90, stop_loss = $2,990 - $10.90 = $2,979.10, risk = $20.90, target = $3,000 + (2 × $20.90) = $3,041.80

**Example 4: ATR Safety Guard - Stop Loss Too Tight**
- **Current Behavior**: Calculated stop_loss distance = $15, ATR(14) = $25, no safety guard applied
- **Problem**: Stop loss is too tight (< 1.5 × ATR = $37.50), will trigger prematurely
- **Expected Behavior**: Expand stop_loss distance to 1.5 × ATR = $37.50 to prevent premature triggering

**Example 5: Email Alert vs History Page Mismatch**
- **Current Behavior**: History API reads stop_loss = $4,530 from database, email alert calculates stop_loss = outer_bottom = $4,477.91 using percentage logic
- **Problem**: Email shows different values than history page, confusing users
- **Expected Behavior**: Email alert reads stop_loss = $4,530 from database (same as history page), ensuring consistency

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- Signal generation with anti-chop filter (1-hour minimum gap, strict alternation BUY→SELL→BUY) must continue to work exactly as before
- Time-distance filtering in history API (1-hour minimum gap between signals) must remain unchanged
- WebSocket alternation checking (block consecutive signals of same type) must remain unchanged
- Email alert recipient filtering (paid subscribers with matching symbol/timeframe preferences) must remain unchanged
- Reversal zone calculator logic for center_price, outer_top, outer_bottom, core_top, core_bottom, is_bullish, label_text must remain unchanged (only stop_loss and target calculation changes)
- Frontend signal history API response structure must remain unchanged (same JSON fields)
- Symbol mapping (XAUUSD → PAXGUSDT, BTCUSD → BTCUSDT, etc.) must remain unchanged
- Binance.US API as data source for historical candles must remain unchanged
- Frontend chart visualization (reversal zones, labels, colors) must remain unchanged (only stop_loss and target values update)
- Database constraint blocking consecutive signals of same type must continue to log INFO messages (not errors)

**Scope:**
All inputs that do NOT involve stop loss or target calculation should be completely unaffected by this fix. This includes:
- Signal detection and reversal zone generation logic
- Anti-chop filtering and alternation enforcement
- WebSocket connection management and broadcasting
- Email alert recipient filtering and template rendering
- Frontend chart rendering and user interface

## Hypothesized Root Cause

Based on the bug description and code analysis, the root causes are:

1. **Naive Percentage-Based Logic**: The `_professional_sl_target()` function in `reversal_zones/reversal_calculator.py` (lines 100-200) uses a fixed percentage approach that doesn't adapt to symbol price levels. High-priced symbols like XAUUSD ($4,500+) and BTCUSD ($100,000+) require absolute point-based buffers, while low-priced symbols need percentage-based buffers.

2. **Missing Market Structure Analysis**: The function doesn't scan backwards to find the last bearish/bullish candle for stop loss placement. It should skip doji candles (|close - open| < 0.01% of price) and use the candle's low/high as the base for stop loss calculation.

3. **Missing ATR Safety Guards**: The function doesn't apply ATR(14) safety guards to ensure stop loss distances are realistic. It should expand distances < 1.5 × ATR and contract distances > 3.0 × ATR.

4. **Incorrect Risk-Reward Calculation**: While the current code attempts a 2:1 ratio, it calculates target based on fixed percentages (4% for BUY) instead of actual risk distance: target = entry + (2 × |entry - stop_loss|).

5. **Email Alert Recalculation**: The `trading/consumers.py` file (lines 670-720) recalculates stop_loss and target values using `outer_bottom` and `outer_top` instead of reading them from the saved ReversalZone record, causing email alerts to show different values than the history page.

6. **Database Data Inconsistency**: Historical ReversalZone records contain incorrect stop_loss and target values calculated using the old percentage-based logic. These need to be recalculated using a Django management command.

## Correctness Properties

Property 1: Bug Condition - Universal Stop Loss Calculation

_For any_ signal generation event where a cryptocurrency symbol generates a BUY or SELL signal, the fixed `_professional_sl_target()` function SHALL calculate stop_loss by: (a) scanning backwards up to 30 candles to find the first bearish candle (for BUY) or bullish candle (for SELL), skipping doji candles where |close - open| < 0.01% of price; (b) for high-priced symbols (price > $1000), applying absolute point-based buffer logic: if 20 ≤ candle_move ≤ 30 → buffer = candle_move + 20, else if candle_move < 20 → buffer = candle_move + 20, else buffer = candle_move; (c) for low-priced symbols (price ≤ $1000), applying percentage-based buffer logic: move_pct = candle_move / entry, if 0.0002 ≤ move_pct ≤ 0.0005 → buffer = candle_move + (entry × 0.0003), else if move_pct < 0.0002 → buffer = candle_move + (entry × 0.0003), else buffer = candle_move; (d) applying ATR(14) safety guards: if calculated SL distance < 1.5 × ATR → expand to 1.5 × ATR, if calculated SL distance > 3.0 × ATR → contract to 3.0 × ATR; (e) calculating target using 2:1 risk-reward ratio: Risk = |entry - stop_loss|, BUY target = entry + (2 × Risk), SELL target = entry - (2 × Risk); (f) rounding all values to 2 decimal places for consistency.

**Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.8, 2.9, 2.10, 2.11**

Property 2: Preservation - Data Consistency Across All Channels

_For any_ signal that is saved to the ReversalZone database, the history API endpoint (`/api/trading/signal-history/<symbol>/`), email alerts (via `trading/consumers.py`), and WebSocket broadcasts SHALL all read stop_loss and target values directly from the saved ReversalZone record without recalculation, ensuring identical values are displayed across all channels (history page, email alerts, WebSocket messages).

**Validates: Requirements 2.5, 2.6, 2.7, 3.1, 3.2, 3.3, 3.4, 3.6**

## Fix Implementation

### Changes Required

Assuming our root cause analysis is correct:

**File**: `reversal_zones/reversal_calculator.py`

**Function**: `_professional_sl_target()`

**Specific Changes**:

1. **Add Symbol Price Level Detection**: 
   - Add logic to detect if symbol is high-priced (price > $1000) or low-priced (price ≤ $1000)
   - This determines whether to use absolute point-based buffers or percentage-based buffers

2. **Implement Backwards Candle Scanning**:
   - Add loop to scan backwards up to 30 candles from signal bar
   - For BUY signals: find first bearish candle (close < open)
   - For SELL signals: find first bullish candle (close > open)
   - Skip doji candles where |close - open| < 0.01% of price
   - Extract candle's low (for BUY) or high (for SELL) as base for stop loss

3. **Implement Universal Buffer Logic**:
   - For high-priced symbols (price > $1000):
     - Calculate candle_move = |open - close| in absolute points
     - If 20 ≤ candle_move ≤ 30: buffer = candle_move + 20
     - Else if candle_move < 20: buffer = candle_move + 20
     - Else: buffer = candle_move
     - BUY: stop_loss = candle_low - buffer
     - SELL: stop_loss = candle_high + buffer
   
   - For low-priced symbols (price ≤ $1000):
     - Calculate move_pct = candle_move / entry_price
     - If 0.0002 ≤ move_pct ≤ 0.0005: buffer = candle_move + (entry × 0.0003)
     - Else if move_pct < 0.0002: buffer = candle_move + (entry × 0.0003)
     - Else: buffer = candle_move
     - BUY: stop_loss = candle_low - buffer
     - SELL: stop_loss = candle_high + buffer

4. **Implement ATR Safety Guards**:
   - Calculate ATR(14) at signal bar (use existing `_atr_series`)
   - Calculate initial stop_loss distance: sl_distance = |entry - stop_loss|
   - If sl_distance < 1.5 × ATR: expand stop_loss to entry ± (1.5 × ATR)
   - If sl_distance > 3.0 × ATR: contract stop_loss to entry ± (3.0 × ATR)
   - Ensure stop_loss never equals entry (minimum distance = 1.5 × ATR)

5. **Implement 2:1 Risk-Reward Target Calculation**:
   - Calculate Risk = |entry - stop_loss|
   - For BUY signals: target = entry + (2 × Risk)
   - For SELL signals: target = entry - (2 × Risk)
   - Remove old percentage-based target calculation (entry × 1.04 for BUY)

6. **Add Decimal Rounding**:
   - Round stop_loss to 2 decimal places: `stop_loss = round(stop_loss, 2)`
   - Round target to 2 decimal places: `target = round(target, 2)`
   - Ensure consistency across all calculations

**File**: `reversal_zones/reversal_calculator.py`

**Function**: `process_ohlcv_data()`

**Specific Changes**:

7. **Update Zone Dictionary Construction**:
   - After calling `_professional_sl_target()`, store stop_loss and target in zone dictionary
   - Ensure outer_top and outer_bottom are set correctly:
     - For BUY: outer_bottom = stop_loss, outer_top = target
     - For SELL: outer_top = stop_loss, outer_bottom = target
   - This ensures database records contain correct values from the moment of creation

**File**: `trading/consumers.py`

**Function**: WebSocket signal broadcasting (around line 670-720)

**Specific Changes**:

8. **Remove Email Alert Recalculation**:
   - Remove lines that calculate `email_stop_loss = outer_bot if is_bull else outer_top`
   - Remove lines that calculate `email_target = outer_top if is_bull else outer_bot`
   - Instead, read stop_loss and target directly from the saved ReversalZone record
   - Update email_payload to use database values: `'stop_loss': zone_record.stop_loss, 'target': zone_record.target`

**File**: `trading/views.py`

**Function**: `get_signal_history()`

**Specific Changes**:

9. **Verify Database Read Logic** (No changes needed - already correct):
   - Confirm that stop_loss and target are read directly from ReversalZone records
   - Confirm that no recalculation occurs in the API endpoint
   - Confirm that values are rounded to 2 decimal places for consistency

**New File**: `reversal_zones/management/commands/recalculate_historical_signals.py`

**Specific Changes**:

10. **Create Django Management Command**:
    - Create new management command to recalculate historical signals
    - Iterate through all ReversalZone records (or filter by date range)
    - For each record:
      - Fetch historical OHLCV data from Binance.US API
      - Call `_professional_sl_target()` with correct parameters
      - Update record's stop_loss and target fields
      - Save record to database
    - Add progress logging (e.g., "Processed 100/500 records")
    - Add error handling for API failures or missing data
    - Add dry-run mode to preview changes without saving

**Database Schema Changes**:

11. **Add stop_loss and target Fields to ReversalZone Model** (if not already present):
    - Add `stop_loss = models.DecimalField(max_digits=20, decimal_places=8, null=True)`
    - Add `target = models.DecimalField(max_digits=20, decimal_places=8, null=True)`
    - Create Django migration: `python manage.py makemigrations`
    - Apply migration: `python manage.py migrate`
    - Note: If fields already exist implicitly through outer_top/outer_bottom, no schema change needed

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples that demonstrate the bug on unfixed code, then verify the fix works correctly and preserves existing behavior.

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bug BEFORE implementing the fix. Confirm or refute the root cause analysis. If we refute, we will need to re-hypothesize.

**Test Plan**: Write tests that generate signals for different symbol types (high-priced, low-priced) and timeframes, then inspect the calculated stop_loss and target values. Run these tests on the UNFIXED code to observe failures and understand the root cause.

**Test Cases**:
1. **High-Priced Symbol Test (XAUUSD)**: Generate BUY signal at $4,569.30, verify stop_loss uses percentage logic (will fail on unfixed code - should show $4,477.91 instead of candle-based $4,530)
2. **High-Priced Symbol Test (BTCUSD)**: Generate SELL signal at $100,000, verify stop_loss uses percentage logic (will fail on unfixed code - should show $102,000 instead of candle-based $99,840)
3. **Low-Priced Symbol Test (ETHUSD)**: Generate BUY signal at $3,000, verify stop_loss uses percentage logic (will fail on unfixed code - may show inconsistent values or duplicates)
4. **ATR Safety Guard Test**: Generate signal where calculated stop_loss distance < 1.5 × ATR, verify no expansion occurs (will fail on unfixed code - should show tight stop that triggers prematurely)
5. **Risk-Reward Ratio Test**: Generate signal and verify target = entry × 1.04 instead of entry + (2 × risk) (will fail on unfixed code - should show fixed percentage instead of risk-based calculation)
6. **Email Alert Consistency Test**: Generate signal, save to database, send email alert, verify email shows different stop_loss than database (will fail on unfixed code - email recalculates using outer_bottom/outer_top)

**Expected Counterexamples**:
- High-priced symbols show percentage-based stop_loss values that don't respect market structure
- Low-priced symbols show inconsistent stop_loss values or duplicate database entries
- Stop loss distances are too tight (< 1.5 × ATR) or too wide (> 3.0 × ATR) without safety guards
- Target values use fixed percentages instead of 2:1 risk-reward ratio
- Email alerts show different stop_loss/target values than history page
- Possible causes: naive percentage logic, missing candle scanning, missing ATR guards, email recalculation

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds, the fixed function produces the expected behavior.

**Pseudocode:**
```
FOR ALL input WHERE isBugCondition(input) DO
  result := _professional_sl_target_fixed(input)
  ASSERT expectedBehavior(result)
END FOR
```

**Expected Behavior Validation:**
- For high-priced symbols (price > $1000): stop_loss uses absolute point-based buffer logic
- For low-priced symbols (price ≤ $1000): stop_loss uses percentage-based buffer logic
- Stop loss is based on last bearish/bullish candle (not arbitrary percentage)
- Stop loss distance respects ATR safety guards (1.5× to 3.0× ATR)
- Target uses 2:1 risk-reward ratio: target = entry + (2 × |entry - stop_loss|)
- All values rounded to 2 decimal places
- Email alerts read stop_loss/target from database (not recalculated)

### Preservation Checking

**Goal**: Verify that for all inputs where the bug condition does NOT hold, the fixed function produces the same result as the original function.

**Pseudocode:**
```
FOR ALL input WHERE NOT isBugCondition(input) DO
  ASSERT originalBehavior(input) = fixedBehavior(input)
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation checking because:
- It generates many test cases automatically across the input domain
- It catches edge cases that manual unit tests might miss
- It provides strong guarantees that behavior is unchanged for all non-buggy inputs

**Test Plan**: Observe behavior on UNFIXED code first for signal generation, anti-chop filtering, alternation enforcement, and WebSocket broadcasting, then write property-based tests capturing that behavior.

**Test Cases**:
1. **Signal Generation Preservation**: Observe that reversal zone detection works correctly on unfixed code, then write test to verify this continues after fix (center_price, is_bullish, label_text unchanged)
2. **Anti-Chop Filter Preservation**: Observe that 1-hour minimum gap and strict alternation work correctly on unfixed code, then write test to verify this continues after fix
3. **WebSocket Broadcasting Preservation**: Observe that WebSocket messages are sent correctly on unfixed code, then write test to verify this continues after fix (only stop_loss/target values change)
4. **Email Alert Recipient Filtering Preservation**: Observe that paid subscribers with matching preferences receive alerts on unfixed code, then write test to verify this continues after fix
5. **Frontend API Response Structure Preservation**: Observe that `/api/trading/signal-history/<symbol>/` returns correct JSON structure on unfixed code, then write test to verify this continues after fix (same fields, only stop_loss/target values change)

### Unit Tests

- Test `_professional_sl_target()` with high-priced symbol (XAUUSD at $4,569.30) - verify absolute point-based buffer logic
- Test `_professional_sl_target()` with low-priced symbol (ETHUSD at $3,000) - verify percentage-based buffer logic
- Test backwards candle scanning - verify it finds first bearish/bullish candle and skips doji candles
- Test ATR safety guards - verify expansion for tight stops (< 1.5 × ATR) and contraction for wide stops (> 3.0 × ATR)
- Test 2:1 risk-reward target calculation - verify target = entry + (2 × risk) for BUY and target = entry - (2 × risk) for SELL
- Test decimal rounding - verify all values rounded to 2 decimal places
- Test email alert data source - verify email reads stop_loss/target from database (not recalculated)
- Test Django management command - verify it recalculates historical signals correctly

### Property-Based Tests

- Generate random high-priced symbols (price > $1000) and verify stop_loss uses absolute point-based buffer logic across many scenarios
- Generate random low-priced symbols (price ≤ $1000) and verify stop_loss uses percentage-based buffer logic across many scenarios
- Generate random ATR values and verify safety guards are applied correctly (1.5× to 3.0× ATR) across many scenarios
- Generate random signal configurations and verify target always uses 2:1 risk-reward ratio across many scenarios
- Generate random signal events and verify email alerts always read from database (not recalculated) across many scenarios
- Generate random signal sequences and verify anti-chop filtering and alternation enforcement continue to work correctly across many scenarios

### Integration Tests

- Test full signal generation flow: generate signal → save to database → verify stop_loss/target calculated correctly
- Test full email alert flow: generate signal → save to database → send email → verify email shows same stop_loss/target as database
- Test full history API flow: generate signal → save to database → call `/api/trading/signal-history/<symbol>/` → verify API returns same stop_loss/target as database
- Test full WebSocket flow: generate signal → save to database → broadcast via WebSocket → verify WebSocket message shows same stop_loss/target as database
- Test Django management command: create historical signals with old logic → run `recalculate_historical_signals` → verify all records updated with new logic
- Test cross-symbol consistency: generate signals for XAUUSD, BTCUSD, ETHUSD, LTCUSD → verify each uses correct buffer logic (absolute vs percentage)
- Test cross-timeframe consistency: generate signals for 15m, 1h, 4h timeframes → verify stop_loss/target calculation works correctly for all timeframes
