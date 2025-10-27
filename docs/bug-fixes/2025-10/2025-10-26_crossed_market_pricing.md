# Bug Fix: Crossed Market Pricing in Liquidity Analyzer

**Business Unit:** Execution | **Status:** Fixed | **Version:** 2.24.0

## Summary
Fixed critical liquidity analyzer bug where BUY orders were generating limit prices that crossed ABOVE the ask price, violating basic market structure. The root cause was computing BOTH buy and sell limit prices simultaneously when only ONE was needed, combined with incorrect volume ratio logic and lack of side-specific pricing.

## Impact
- **Severity:** Critical (execution correctness)
- **System:** Smart execution strategy with liquidity-aware pricing
- **Symptom:** "Ask price < bid price" warnings for large orders
- **Detection:** Production logs showing crossed market warnings

## Root Causes (Multiple Issues Fixed)

### Issue 1: Computing Both Sides When Only One Needed
**Problem:** Original `_calculate_volume_aware_prices()` computed BOTH buy and sell limit prices regardless of which side was actually being traded.

**Why This Mattered:**
- Caller only needed ONE side (BUY or SELL)
- Computing both created opportunities for self-crossing
- Fallback values for unused side triggered false invariant violations

**Fix:** Added `side` parameter to compute only the requested side:
```python
def _calculate_volume_aware_prices(
    self, quote: QuoteModel, order_size: float, side: str | None = None
) -> dict[str, float]:
    """Calculate optimal limit price(s) based on volume analysis.

    Args:
        side: "BUY" or "SELL". If specified, only computes that side.
    """
```

### Issue 2: Incorrect Anchoring and Crossing Logic
**Problem:** Original logic set BUY limits relative to bid AND allowed crossing above ask:

```python
# OLD (BROKEN): BUY orders anchored to bid, could cross above ask
if ask_volume_ratio > 0.8:
    recommended_bid = ask_price + (self.tick_size * 2)  # ❌ Crosses ABOVE ask!
```

**Correct Logic:**
- BUY orders consume from ASK side (you buy FROM sellers)
- BUY limit must be ≤ ask (never cross above)
- SELL orders consume from BID side (you sell TO buyers)
- SELL limit must be ≥ bid (never cross below)

**Fix:** Separate helper methods with correct anchoring:
```python
def _calculate_buy_limit(self, ask_price, ask_volume_ratio, quantize):
    """BUY orders anchor to ask_price, never cross above."""
    base_limit = ask_price  # Start at ask

    if ask_volume_ratio > 0.8:  # Large order needs certainty
        limit = base_limit  # Price AT ask (not above)
    elif ask_volume_ratio > 0.3:
        limit = base_limit  # Price AT ask
    else:
        limit = quantize(ask_price - self.tick_size)  # Try 1 tick improvement

    return quantize(max(limit, Decimal("0.01")))

def _calculate_sell_limit(self, bid_price, bid_volume_ratio, quantize):
    """SELL orders anchor to bid_price, never cross below."""
    base_limit = bid_price  # Start at bid

    if bid_volume_ratio > 0.8:  # Large order needs certainty
        limit = base_limit  # Price AT bid (not below)
    elif bid_volume_ratio > 0.3:
        limit = base_limit  # Price AT bid
    else:
        limit = quantize(bid_price + self.tick_size)  # Try 1 tick improvement

    return quantize(max(limit, Decimal("0.01")))
```

### Issue 3: Misleading Variable Names
**Problem:** Variables named `recommended_bid` and `recommended_ask` implied market-making quotes, but these are actually **limit prices for taking liquidity**.

**Fix:** Renamed to `buy_limit` and `sell_limit` throughout, with clear documentation that these are limit prices for orders, not quotes.

### Issue 4: False Invariant Violations
**Problem:** When computing only SELL side, fallback BUY value was set to `bid_price`. For large SELL orders pricing at `bid_price`, this created:
```
buy_limit (fallback) = 25.00
sell_limit (computed) = 25.00
→ Triggers "INVARIANT VIOLATION" and emergency widening to 25.01
```

**Fix:** Only enforce buy < sell invariant in legacy mode (side=None) where both are meaningful:
```python
# Enforce invariant ONLY in legacy mode where both sides are computed
if side is None and buy_limit >= sell_limit:
    logger.error("INVARIANT VIOLATION...")
    sell_limit = quantize(buy_limit + self.tick_size)
```

## Example: SOXS Reproduction Case

**Before Fix:**
```
Quote: bid=4.14, ask=4.15, bid_size=37, ask_size=70
Order: BUY 4478 shares (6397% of ask liquidity!)

Calculation:
- ask_volume_ratio = 4478/70 = 64x (huge)
- Original logic: recommended_bid = 4.15 + 0.02 = 4.17 ❌ CROSSED!
- Sanity check adjusted to 4.16, still crossed
```

**After Fix:**
```
Quote: bid=4.14, ask=4.15, bid_size=37, ask_size=70
Order: BUY 4478 shares

Calculation:
- ask_volume_ratio = 4478/70 = 64x → Large order (>80%)
- _calculate_buy_limit: limit = ask_price = 4.15 ✅ AT ask
- Result: BUY limit = 4.15 (no crossing, proper fill certainty)
```

## Testing
Comprehensive test suite created with 10 tests including:
- ✅ SOXS reproduction case (exact scenario from logs)
- ✅ BUY orders never cross above ask (all order sizes)
- ✅ SELL orders never cross below bid (all order sizes)
- ✅ Tick quantization (no floating point errors)
- ✅ Large order pricing (>80% liquidity → AT quote)
- ✅ Small order pricing (<30% liquidity → improvement attempts)
- ✅ Property-based tests (Hypothesis: 200+ random scenarios)

All tests pass with correct market-respecting behavior.

## Files Changed
- `the_alchemiser/execution_v2/utils/liquidity_analysis.py`
  - Added `side` parameter to `analyze_liquidity()` and `_calculate_volume_aware_prices()`
  - Split pricing logic into `_calculate_buy_limit()` and `_calculate_sell_limit()`
  - Fixed invariant enforcement to apply only in legacy mode
  - Corrected volume ratio logic and anchoring

- `the_alchemiser/execution_v2/core/smart_execution_strategy/pricing.py`
  - Updated to pass `side` parameter to `analyze_liquidity()`

- `tests/unit/execution_v2/test_liquidity_analysis_fix.py` (NEW)
  - 10 comprehensive tests verifying correct no-cross behavior

## Deployment Notes
- **Backward Compatible:** `side` parameter is optional (defaults to `None` for legacy behavior)
- **Production Impact:** Eliminates crossed market warnings
- **Performance:** Slightly faster (computes only needed side)
- **Version:** 2.24.0 (MINOR bump due to API addition)

## References
- Original Issue: Crossed market warnings in production logs (SOXS example)
- User Feedback: "the main fix is still wrong... you're bidding above the current ask"
- Architecture: Copilot instructions emphasize using Decimal for money, never crossing spreads
