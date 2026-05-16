# URGENT: Update Stop Loss & Target Values

## Problem Fixed
The previous implementation was using percentage-based stop loss which resulted in unrealistically tight stops (0.26% - 0.33%).

## New Implementation
- **BUY signals**: Finds previous bearish candle, uses `candle_low - 20 points` as stop loss
- **SELL signals**: Finds previous bullish candle, uses `candle_high + 20 points` as stop loss
- **Small candles**: If candle moved < 30 points, adds extra 20-point buffer
- **Target**: Always 2:1 Risk:Reward ratio
- **ATR guards**: Minimum 1.5× ATR, maximum 3× ATR (tighter than before)

## Expected Results
After update, stop loss distances should be:
- **Minimum**: ~1.5× ATR (much wider than 0.26%)
- **Typical**: 20-40 points from entry (for small assets like LTC, ETH)
- **BTC**: 40-100 points from entry
- **Gold**: 30-60 points from entry

## Commands to Run on AWS EC2

```bash
# 1. First, test with dry-run to see what will change
docker-compose exec django python manage.py recalculate_historical_sl_target --dry-run --limit 10

# 2. If dry-run looks good, update ALL records
docker-compose exec django python manage.py recalculate_historical_sl_target

# 3. Restart services to apply changes
docker-compose restart django celery_worker celery_beat
```

## Verification
After running the update:
1. Check history page - stop loss should be much wider (1-3% from entry)
2. Example: LTCUSD at $56.84 should have SL around $55.50-$56.00 (not $56.65)
3. Example: ETHUSD at $2,220 should have SL around $2,180-$2,200 (not $2,214)

## Files Modified
- `reversal_zones/reversal_calculator.py` - Completely rewrote `_professional_sl_target()` function
  - Removed percentage-based logic
  - Added fixed 20-point buffer
  - Added extra 20-point buffer for small-move candles
  - Changed ATR guards from 2×-5× to 1.5×-3×
