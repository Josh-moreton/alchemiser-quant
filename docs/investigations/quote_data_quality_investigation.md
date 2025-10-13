# Quote Data Quality Investigation

**Date:** 2025-10-10  
**Issue:** Investigate quote problems and lack of data provider redundancy  
**Status:** ✅ Resolved  

## Problem Statement

Recurring issues with quote data quality leading to order placement failures:
- Streaming quotes showed valid prices (bid=269.58, ask=270.73 for BULZ)
- Liquidity analysis produced negative recommended prices (-0.01, -0.02)
- Orders failed with "cost basis must be >= minimal amount of order 1"

## Root Cause Analysis

### Primary Issue
The bug was in `the_alchemiser/execution_v2/utils/liquidity_analysis.py` in the `_calculate_volume_aware_prices` method:

```python
# Line 207: Aggressive pricing for heavy bid side
if imbalance < -0.2:
    recommended_bid = min(recommended_bid + self.tick_size, ask_price - self.tick_size)
```

**Problem:** If `ask_price` was corrupted or zero (due to upstream data quality issues), the expression `ask_price - self.tick_size` could produce negative values like `-0.01`.

**Similar issue on line 212 for ask side:**
```python
elif imbalance > 0.2:
    recommended_ask = max(recommended_ask - self.tick_size, bid_price + self.tick_size)
```

### Why This Occurred
1. No early validation of quote prices before arithmetic operations
2. Aggressive pricing logic assumed valid positive prices
3. Fallback validation at lines 223-235 caught negatives but used $0.01 minimum, causing order failures

### Data Flow Analysis
The corruption happened somewhere between:
1. Streaming quote reception (correct: bid=269.58, ask=270.73)
2. Liquidity analysis execution (incorrect: leading to -0.01, -0.02)

Possible causes:
- Stale quote data overwriting fresh data in concurrent environment
- Attribute access on wrong QuoteModel variant (legacy vs. market_data)
- Type coercion issues during Decimal/float conversions
- Race condition in quote storage/retrieval

## Fixes Implemented

### 1. Early Validation (Line 182-193)
```python
# Early validation: Ensure quote prices are positive before any calculations
if quote.bid_price <= 0 or quote.ask_price <= 0:
    logger.error(
        f"Invalid quote prices for {quote.symbol}: "
        f"bid_price={quote.bid_price}, ask_price={quote.ask_price}. "
        f"Cannot calculate volume-aware prices with non-positive values."
    )
    # Return minimum valid prices as emergency fallback
    min_price = Decimal("0.01")
    return {"bid": float(min_price), "ask": float(min_price)}
```

### 2. Defensive Aggressive Pricing (Lines 236-258)
```python
# If heavy bid side (imbalance < -0.2), be more aggressive on buys
if imbalance < -0.2:
    # Ensure we don't create negative prices
    aggressive_bid_limit = ask_price - self.tick_size
    if aggressive_bid_limit > 0:
        recommended_bid = min(recommended_bid + self.tick_size, aggressive_bid_limit)
        logger.debug(f"Heavy bid side detected, adjusting buy price to {recommended_bid}")
    else:
        logger.warning(
            f"Cannot apply heavy bid side adjustment for {quote.symbol}: "
            f"ask_price ({ask_price}) too small for tick adjustment"
        )
```

### 3. Enhanced Diagnostic Logging (Lines 74-101)
```python
# Enhanced logging with full quote details for suspicious quotes
if quote.bid_price <= 0 or quote.ask_price <= 0 or quote.bid_price > quote.ask_price:
    logger.error(
        f"Suspicious quote detected for {quote.symbol}: "
        f"bid_price={quote.bid_price}, ask_price={quote.ask_price}, "
        f"bid_size={quote.bid_size}, ask_size={quote.ask_size}, "
        f"timestamp={quote.timestamp}"
    )
```

## Data Provider Redundancy

### Current Architecture ✅
The system already implements robust data provider redundancy:

1. **Primary Source:** WebSocket streaming quotes
   - Real-time bid/ask updates
   - Low latency (~100ms)
   - Continuous market depth data

2. **Validation Layer:** REST API cross-check
   - Suspicious quote detection triggers REST validation
   - Compares streaming vs. REST mid-prices
   - Uses REST if difference > 10%

3. **Fallback Source:** REST API
   - Used when streaming unavailable
   - Reliable but higher latency (~200-500ms)
   - No real-time market depth

### Suspicious Quote Detection
`_is_streaming_quote_suspicious()` checks for:
- Negative prices
- Inverted spreads (ask < bid)
- Unreasonably low prices (< $0.01)
- Excessive spreads (> 10%)

### Validation Flow
```
Streaming Quote Received
         ↓
Is Suspicious? → NO → Use Streaming Quote
         ↓ YES
   Validate with REST
         ↓
  REST Quote Valid? → YES → Use REST Quote
         ↓ NO
Use Streaming Quote (with warning)
```

## Test Coverage

Added comprehensive tests in `tests/execution_v2/test_liquidity_analysis.py`:

1. **test_prevents_negative_prices_with_zero_quote_prices**
   - Validates handling of zero prices
   - Ensures minimum $0.01 fallback

2. **test_prevents_negative_prices_with_negative_quote_prices**
   - Validates handling of negative prices
   - Prevents propagation of invalid data

3. **test_normal_quotes_produce_positive_recommended_prices**
   - Regression test with actual BULZ quote
   - Validates normal operation produces sensible prices

4. **test_aggressive_pricing_doesnt_produce_negative_values**
   - Tests heavy imbalance scenarios
   - Validates aggressive adjustments remain positive

5. **test_small_price_stocks_handled_safely**
   - Tests low-priced stocks ($0.50-$0.52)
   - Ensures tick adjustments don't go negative

## Recommendations

### Immediate Actions
1. ✅ Deploy fix to prevent negative prices
2. ✅ Enhanced logging for diagnostics
3. 🔄 Monitor logs for patterns of suspicious quotes
4. 🔄 Investigate if specific symbols trigger issues more frequently

### Short-term Improvements
1. **Enhanced Quote Validation at Source**
   - Add validation in `RealTimePriceStore.update_quote_data`
   - Reject quotes with negative/zero prices immediately
   - Log rejected quotes with full context

2. **Quote Freshness Monitoring**
   - Track quote age in milliseconds
   - Alert on stale quotes (> 5 seconds old)
   - Implement quote TTL (time-to-live) mechanism

3. **Data Quality Metrics**
   - Count suspicious quotes per symbol
   - Track REST validation trigger rate
   - Monitor quote rejection rate

### Long-term Considerations
1. **Multiple Data Providers**
   - Add secondary provider (e.g., Polygon.io, IEX)
   - Implement quote consensus algorithm
   - Use median of multiple sources for critical decisions

2. **Quote Sanity Boundaries**
   - Define acceptable price ranges per symbol
   - Reject quotes outside historical ranges
   - Implement circuit breakers for extreme moves

3. **Streaming Reliability Improvements**
   - Implement WebSocket health checks
   - Auto-reconnect on quality degradation
   - Track message latency and gaps

## Additional Fix: Partial Quote Handling

### Problem
Streaming quotes sometimes arrive with only bid OR ask available (the other side is None). The original code rejected these entirely:

```python
# Old code - line 361
if quote_values.bid_price is not None and quote_values.ask_price is not None:
    # Only update if BOTH are present
```

This caused valid partial quotes to be ignored, potentially leaving stale data in the system.

### Solution
Implemented the same fallback logic as the REST API (already present in `market_data_service.py` lines 206-215):

```python
# New code - lines 361-387
if bid_price is not None and ask_price is not None:
    # Both available - use as-is
    pass
elif bid_price is not None:
    # Only bid available - use bid for both sides
    ask_price = bid_price
elif ask_price is not None:
    # Only ask available - use ask for both sides
    bid_price = ask_price
else:
    # Both None - skip update, keep previously stored quote
    return
```

### Behavior
- **Bid-only quote:** Uses bid price for both bid and ask sides
- **Ask-only quote:** Uses ask price for both bid and ask sides
- **Both None:** Keeps previously stored quote (doesn't update)
- **Both present:** Updates normally with both values

This ensures we always have valid quote data even when the data provider sends partial updates, which is common in real-time streaming scenarios.

## Version Update
- **Previous:** 2.20.6
- **Current:** 2.20.7 (PATCH: Bug fixes for negative price handling + partial quote handling)

## Related Files
- `the_alchemiser/execution_v2/utils/liquidity_analysis.py` - Primary fix location
- `the_alchemiser/execution_v2/core/smart_execution_strategy/quotes.py` - Data provider redundancy
- `the_alchemiser/shared/services/real_time_pricing.py` - Streaming quote ingestion
- `tests/execution_v2/test_liquidity_analysis.py` - Test coverage

## Monitoring Points
After deployment, monitor for these log patterns:

### Success Indicators
- No more "Invalid recommended bid/ask price" warnings
- No order failures with "cost basis must be >= minimal amount"
- Suspicious quote detection triggers REST validation successfully

### Warning Indicators
- Frequent "Invalid quote prices" errors → upstream data quality issue
- Frequent "Cannot apply heavy [bid|ask] side adjustment" → investigate tick size logic
- Frequent REST validation triggers → streaming data quality degraded

### Critical Indicators
- Streaming quotes consistently suspicious → provider issue, increase REST usage
- Emergency $0.01 fallback frequently used → investigate data corruption source
