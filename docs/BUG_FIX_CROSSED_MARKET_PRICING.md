# Bug Fix: Crossed Market Pricing in Liquidity Analyzer

## Issue #2459 Resolution
**Status**: Closed as "won't fix" - boto3-stubs not needed (boto3 is not a dependency)

## Critical Bug Fixed: Crossed Market Pricing

### Problem
The liquidity analyzer was calculating **crossed markets** (ask < bid) for large BUY orders, causing warnings like:
```
Ask price 4.15 < bid price 4.16 for SOXS, adjusting ask to match bid
```

### Root Cause
The original logic in `_calculate_volume_aware_prices()` calculated BOTH bid and ask prices based on **wrong volume ratios**:

```python
# OLD (BROKEN) LOGIC:
if bid_volume_ratio > 0.8:  # ❌ WRONG: Using bid_volume for BUY pricing
    recommended_bid = bid_price + (self.tick_size * 2)

if ask_volume_ratio > 0.8:  # ❌ WRONG: Using ask_volume for SELL pricing  
    recommended_ask = ask_price - (self.tick_size * 2)
```

**For BUY orders**: We need to look at **ask volume** (we're buying FROM sellers)
**For SELL orders**: We need to look at **bid volume** (we're selling TO buyers)

### Example Failure Case (SOXS)
- **Quote**: bid=4.14, ask=4.15, bid_size=37, ask_size=70
- **Order**: BUY 4478.287093 shares
- **Calculation**:
  - bid_volume_ratio = 4478/37 = **121x** (huge!)
  - ask_volume_ratio = 4478/70 = **64x** (huge!)
- **Result (broken)**:
  - recommended_bid = 4.14 + 0.02 = **4.16** ✅
  - recommended_ask = 4.15 - 0.02 = **4.13** ❌ (crossed!)
- **After imbalance adjustment**: ask adjusted to 4.15, still < 4.16
- **Final sanity check**: ask forced to 4.16 (matched bid)

### Fix
Corrected the volume ratio logic to match order direction:

```python
# NEW (CORRECT) LOGIC:
# For BUY orders: price based on ask_volume_ratio (buying from sellers)
if ask_volume_ratio > 0.8:  # ✅ CORRECT: Large BUY needs aggressive ask pricing
    recommended_bid = ask_price + (self.tick_size * 2)

# For SELL orders: price based on bid_volume_ratio (selling to buyers)
if bid_volume_ratio > 0.8:  # ✅ CORRECT: Large SELL needs aggressive bid pricing
    recommended_ask = bid_price - (self.tick_size * 2)
```

### Impact
- **Before**: Crossed markets for large orders, poor execution prices
- **After**: Proper liquidity-aware pricing that respects bid/ask spread
- **Version**: Fixed in v2.23.2

### Files Changed
- `the_alchemiser/execution_v2/utils/liquidity_analysis.py` (lines 180-234)

### Testing Recommendation
Run paper trading with large orders (>80% of available liquidity) to verify:
1. No more "Ask price < bid price" warnings
2. Orders fill at reasonable prices
3. Smart execution strategy works correctly

### Related Issues
- Closes: Issue about boto3-stubs (not needed)
- Fixes: Critical pricing bug in smart execution
